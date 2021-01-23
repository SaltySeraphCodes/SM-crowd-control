const fs = require("fs");
const fse = require('fs-extra')
const path = require("path");
const fetch = require("node-fetch");
const extract = require('extract-zip')
const domain = "https://backend-01-prd.steamworkshopdownloader.io";

let startArgs = []

process.argv.forEach(function (val, index, array) {
    if (index > 1) {
        startArgs.push(val);
    }
});

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, 1000));
}

async function request(fileid) {
    const body = {
        "publishedFileId": fileid,
        "collectionId": null,
        "extract": true,
        "hidden": false,
        "direct": false,
        "autodownload": false
    }

    return fetch(`${domain}/api/download/request`, {
        method: "post",
        body: JSON.stringify(body),
        headers: { "Content-Type": "application/json" }
    })
    .then(res => res.json())
    .then(json => json.uuid);
}

async function waitForPrepaired(uuid, interval = 1000) {
    const body = {
        "uuids": [uuid]
    }

    return fetch(`${domain}/api/download/status`, {
        method: "post",
        body: JSON.stringify(body),
        headers: { "Content-Type": "application/json" }
    })
    .then(res => res.json())
    .then(json => {
        console.log(json);

        if (json[uuid].status === "prepared") {
            return uuid;
        } else {
            return sleep(interval).then(() => waitForPrepaired(uuid, interval));
        }
    });
}

async function transmit(uuid, filename) {
    return fetch(`${domain}/api/download/transmit?uuid=${uuid}`)
    .then(res => {
        console.log(res);

        return new Promise((resolve, reject) => {
            const dest = fs.createWriteStream(filename);
            res.body.pipe(dest);
            dest.on("close", () => resolve());
            dest.on("error", reject);
        });
    });
}

async function download(fileid, dest) {
    return await transmit(await waitForPrepaired(await request(fileid)), path.join(dest, `${fileid}.zip`));
}

(async () =>
{
    try {
        const dest = path.join(process.cwd(), "downloads");

        if (!fs.existsSync(dest)) {
            fs.mkdirSync(dest);
        }
        else {
            fs.rmdirSync(dest, { recursive: true });
            sleep(100);
            fs.mkdirSync(dest);
        }

        await download(parseInt(startArgs[0]), dest);

        target = path.join(dest, startArgs[0]);

        if (!fs.existsSync(target)) {
            fs.mkdirSync(target);
        }
        else {
            fs.rmdirSync(target, { recursive: true });
            fs.mkdirSync(target);
        }

        zip = path.join(dest, startArgs[0] + ".zip");
        await extract(zip, { dir: target });

        fs.unlinkSync(zip);

        /*
        blueprintPath = path.join(startArgs[1], "Survival", "LocalBlueprints", startArgs[0] + ".blueprint");
        console.log(path.join(target, "blueprint.json"))
        fse.move(path.join(target, "blueprint.json"), blueprintPath);
        */

        process.exit();
    }
    catch (err) {
        process.exit(69);
    }
})();
