'use strict';
importScripts("https://cdn.jsdelivr.net/npm/comlink@4.4.1/dist/umd/comlink.min.js");
importScripts("https://cdn.jsdelivr.net/pyodide/v0.23.3/full/pyodide.js")
importScripts("utils.js")

let inputFile = "input.p8";
let inputSrcDir = "input.dir";
let outputFile = "output.unk";
let previewFile = "preview.p8";
let scriptFile = "script.py";

let outputCapture = undefined;
let initProgress = 0;

function shrinko8(args, fail) {
    try {
        outputCapture = "";
        let exitCode = shrinko8_main(args);
        if (!exitCode) {
            exitCode = 0;
        } else if (fail) {
            throw new Error();
        }
        return [exitCode, outputCapture]
    } catch (e) {
        console.error(e);
        if (!e.message || (e instanceof pyodide.ffi.PythonError && e.type == "SystemExit")) {
            e.message = outputCapture; // rest doesn't matter
        } else {
            e.message += "\n" + outputCapture;
        }
        throw e;
    } finally {
        outputCapture = undefined
    }
}

function onOutput(msg, loggerFunc) {
    loggerFunc(msg);
    if (outputCapture != undefined) {
        outputCapture += msg + "\n";
    }
}

async function initShrinko() {
    try {
        initProgress = 30;
        self.pyodide = await loadPyodide({
            fullStdLib: false,
            stdout: msg => onOutput(msg, console.info),
            stderr: msg => onOutput(msg, console.warn),
        });
        initProgress = 60;

        self.fs = pyodide.FS
        fs.writeFile(inputFile, "");

        await pyodide.loadPackage("pillow");
        initProgress = 90;

        let response = await fetch("shrinko8.zip");
        await pyodide.unpackArchive(await response.arrayBuffer(), "zip");

        let module = pyodide.pyimport("shrinko8");
        self.shrinko8_main = module.main
        initProgress = 100;
    } catch (e) {
        console.error(e);
        initProgress = -1;
    }
}

let initPromise = initShrinko();

let shlex_module;
function shlex(str) {
    if (!shlex_module) {
        shlex_module = pyodide.pyimport("shlex");
    }

    return shlex_module.split(str).toJs()
}

function rmdirRec(path) {
    for (let file of fs.readdir(path)) {
        if (file == "." || file == "..") {
            continue;
        }

        let child = joinPath(path, file);
        if (fs.isDir(fs.stat(child).mode)) {
            rmdirRec(child);
            fs.rmdir(child);
        } else {
            fs.unlink(child);
        }
    }
}

function mkdirParentRec(path) {
    let result = fs.analyzePath(path);
    if (!result.exists && !result.parentExists) {
        let parentPath = getParentDir(path);
        if (parentPath) {
            mkdirParentRec(parentPath);
            fs.mkdir(parentPath);
        }
    }
}

let api = {
    loadInputFiles: async (files, main) => {
        await initPromise;

        let mainExt = getLowExt(main);
        if ((mainExt == "p8" || mainExt == "lua") && files.length == 1) {
            // simple case - no conversion/preprocessing is needed or wanted.
            let [_, data] = files[0];
            fs.writeFile(inputFile, new Uint8Array(data));
            return fs.readFile(inputFile, {encoding: "utf8"});
        } else {
            // copy entire files list and convert/preprocess to p8
            if (fs.analyzePath(inputSrcDir).exists) {
                rmdirRec(inputSrcDir);
            }
            for (let [relpath, data] of files) {
                let path = joinPath(inputSrcDir, relpath);
                mkdirParentRec(path);
                fs.writeFile(path, new Uint8Array(data));
            }
        
            let mainPath = joinPath(inputSrcDir, main);
            shrinko8([mainPath, inputFile], true);
            return fs.readFile(inputFile, {encoding: "utf8"});
        }
    },

    updateInputFile: async (text) => {
        await initPromise; // includes fs init
        fs.writeFile(inputFile, text);
    },
    updateScriptFile: async (text) => {
        await initPromise; // includes fs init
        fs.writeFile(scriptFile, text);
    },
    getProgress: () => initProgress,

    runShrinko: async (args, argStr, useScript, encoding) => {
        await initPromise;

        let cmdline = [inputFile];
        if (encoding) {
            cmdline.push(outputFile);
        }
        cmdline.push(...args);
        if (argStr) {
            cmdline.push(...shlex(argStr));
        }
        if (useScript) {
            cmdline.push("--script", scriptFile);
        }
        if (encoding == "binary") {
            cmdline.push("--extra-output", previewFile);
        }

        let [code, stdout] = shrinko8(cmdline);

        let output, preview;
        if (code == 0) {
            if (encoding) {
                output = fs.readFile(outputFile, {encoding});
            }
            if (encoding == "binary") {
                preview = fs.readFile(previewFile, {encoding: "utf8"});
            }
        }

        return [code, stdout, output, preview];
    },

    runTests: async () => {
        // current status: zlib is different so tests that generate pngs fail at compare time
        // (should I change tests to compare pngs by pixels?)
        // (also, currently always throws SystemExit)
        await initPromise;
        
        let response = await fetch("shrinko8_test.zip");
        await pyodide.unpackArchive(await response.arrayBuffer(), "zip");

        let runpy = pyodide.pyimport("runpy");
        try {
            outputCapture = "";
            runpy.run_module("run_tests", undefined, "__main__");
            throw new Error("shouldn't reach here"); // due to sys.exit
        } catch (e) {
            console.error(e);
            e.message += "\n" + outputCapture;
            throw e;
        } finally {
            outputCapture = null;
        }
    },
}

Comlink.expose(api);
