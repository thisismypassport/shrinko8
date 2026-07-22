// Get the lowercase extension of a path
export function getLowExt(path) {
    let match = path.match(/\.([^\.\/]+)$/);
    return match ? match[1].toLowerCase() : "";
}

// Remove all extensions of a path
export function getWithoutAllExts(path) {
    let match = path.match(/(.*?)\.[^\/]*$/);
    return match ? match[1] : path;
}

export function getBaseName(path) {
    let match = path.match(/\/([^\/]+)$/);
    return match ? match[1] : path;
}

export function getParentDir(path) {
    let match = path.match(/(.*)\/[^\/]+$/);
    return match ? match[1] : "";
}

export function joinPath(a, b) {
    if (!a || b.startsWith("/")) {
        return b;
    } else {
        return a + "/" + b;
    }
}

export function isFormatText(fmt) {
    return fmt == "lua" || fmt == "p8" || fmt == "p64";
}
export function isFormatImg(fmt) {
    return fmt == "png";
}
export function isFormatExport(fmt) {
    return fmt == "pod" || fmt == "js" || fmt == "dat" || fmt == "html" || fmt == "bin";
}
export function isFormatNeedZip(fmt) {
    return fmt == "bin" || fmt == "dir";
}
export function isFormatUrl(fmt) {
    return fmt == "url";
}
