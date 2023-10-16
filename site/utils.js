'use strict';

// Get the lowercase extension of a path
function getLowExt(path) {
    let match = path.match(/\.([^\.\/]+)$/);
    return match ? match[1].toLowerCase() : "";
}

// Remove all extensions of a path
function getWithoutAllExts(path) {
    let match = path.match(/(.*?)\.[^\/]*$/);
    return match ? match[1] : path;
}

function getBaseName(path) {
    let match = path.match(/\/([^\/]+)$/);
    return match ? match[1] : path;
}

function getParentDir(path) {
    let match = path.match(/(.*)\/[^\/]+$/);
    return match ? match[1] : "";
}

function joinPath(a, b) {
    if (!a || b.startsWith("/")) {
        return b;
    } else {
        return a + "/" + b;
    }
}

function isFormatText(fmt) {
    return fmt == "lua" || fmt == "p8";
}
function isFormatImg(fmt) {
    return fmt == "png";
}
function isFormatExport(fmt) {
    return fmt == "pod" || fmt == "js" || fmt == "bin";
}
function isFormatNeedZip(fmt) {
    return fmt == "bin";
}
function isFormatUrl(fmt) {
    return fmt == "url";
}
