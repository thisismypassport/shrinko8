'use strict';

// Get the lowercase extension of a path
function getLowExt(path) {
    let match = path.match(/\.([^\.]+)$/);
    return match ? match[1].toLowerCase() : "";
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
