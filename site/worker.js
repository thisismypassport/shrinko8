'use strict';
importScripts("https://cdn.jsdelivr.net/npm/comlink@4.4.1/dist/umd/comlink.min.js");
importScripts("https://cdn.jsdelivr.net/pyodide/v0.23.3/full/pyodide.js")

let inputFile = "input.p8";
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

let api = {
    loadInputFile: async (input, name) => {
        await initPromise;
        let ext = name.match(/\.([^\.]+)$/)[1];

        if (ext == "p8" || ext == "lua") {
            fs.writeFile(inputFile, new Uint8Array(input));
            return fs.readFile(inputFile, {encoding: "utf8"});
        } else {
            let fileInputFile = `file-input.${ext}`;
            fs.writeFile(fileInputFile, new Uint8Array(input));

            shrinko8([fileInputFile, inputFile], true);
            return fs.readFile(inputFile, {encoding: "utf8"});
        }
    },

    updateInputFile: (text) => {
        fs.writeFile(inputFile, text);
    },
    updateScriptFile: (text) => {
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
        if (encoding) {
            output = fs.readFile(outputFile, {encoding});
        }
        if (encoding == "binary") {
            preview = fs.readFile(previewFile, {encoding: "utf8"});
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
