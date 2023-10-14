'use strict';
importScripts("https://cdn.jsdelivr.net/npm/comlink@4.4.1/dist/umd/comlink.min.js");
importScripts("https://cdn.jsdelivr.net/pyodide/v0.23.3/full/pyodide.js")
importScripts("utils.js")

let inputFile = "input.p8";
let inputSrcDir = "input.dir";
let extraInputFileTmpl = "extrainput#.p8"
let outputFile = "output.unk";
let outputDir = "output.dir";
let previewFile = "preview.p8";
let scriptFile = "script.py";
let pico8Dat = "pico8.dat";

let outputCapture = undefined;
let initProgress = 0;
let hasPico8Dat = false;

function run_main(main, args, fail) {
    try {
        outputCapture = "";
        let exitCode = main(args);
        if (fail) {
            if (exitCode) {
                throw new Error();
            }
            return outputCapture;
        } else {
            return [exitCode ? exitCode : 0, outputCapture];
        }
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

function shrinko8(args, fail) {
    return run_main(self.shrinko8_main, args, fail)
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

let shutil_module;
function makeArchive(outputFile, ...args) {
    if (!shutil_module) {
        shutil_module = pyodide.pyimport("shutil");
    }

    let zipName = shutil_module.make_archive(outputFile, ...args)
    if (outputFile !== zipName) {
        shutil_module.move(zipName, outputFile)
    }
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

function rmdirRecIfNeeded(dir) {
    if (fs.analyzePath(dir).exists) {
        rmdirRec(dir);
    }
}

function copyInputs(files, main) {
    rmdirRecIfNeeded(inputSrcDir);
    for (let [relpath, data] of files) {
        let path = joinPath(inputSrcDir, relpath);
        mkdirParentRec(path);
        fs.writeFile(path, new Uint8Array(data));
    }

    return joinPath(inputSrcDir, main);
}

let api = {
    loadInputFiles: async (files, main, subfile, extras) => {
        await initPromise;

        let mainExt = getLowExt(main);
        if (isFormatText(mainExt) && files.size == 1 && subfile == null && !extras) {
            // simple case - no conversion/preprocessing is needed or wanted.
            let data = files.values().next().value;
            fs.writeFile(inputFile, new Uint8Array(data));
            return fs.readFile(inputFile, {encoding: "utf8"});
        } else {
            // copy entire files list and convert/preprocess to p8
            let mainPath = copyInputs(files, main);
            let args = [mainPath, inputFile];
            if (subfile != null) {
                args.push("--cart", subfile)
            }
            shrinko8(args, true);
            let result = fs.readFile(inputFile, {encoding: "utf8"});
            
            // also convert/preprocess extra files
            let extraI = 0;
            if (extras) {
                for (let extra of extras) {
                    let extraInputFile = extraInputFileTmpl.replace("#", extraI++);
                    shrinko8([joinPath(inputSrcDir, extra), extraInputFile], true);
                }
            }

            return result;
        }
    },
    listInputFile: async (files, main) => {
        await initPromise;
        let mainPath = copyInputs(files, main);
        let output = shrinko8([mainPath, "--list"], true);
        return output.split("\n").filter(l => l);
    },

    updateInputFile: async (text) => {
        await initPromise; // includes fs init
        fs.writeFile(inputFile, text);
    },
    updateScriptFile: async (text) => {
        await initPromise; // includes fs init
        fs.writeFile(scriptFile, text);
    },
    updatePico8Dat: async (data) => {
        await initPromise; // includes fs init
        fs.writeFile(pico8Dat, new Uint8Array(data));
        hasPico8Dat = true;
    },
    
    getProgress: () => initProgress,
    getVersion: async () => {
        await initPromise;
        return shrinko8(["--version"], true);
    },

    runShrinko: async (args, argStr, useScript, encoding, usePreview, doZip, extraNames) => {
        await initPromise;

        let cmdline = [inputFile];
        if (encoding) {
            if (doZip) {
                rmdirRecIfNeeded(outputDir);
                cmdline.push(outputDir);
            } else {
                cmdline.push(outputFile);
            }
        }
        cmdline.push(...args);
        if (argStr) {
            cmdline.push(...shlex(argStr));
        }
        if (useScript) {
            cmdline.push("--script", scriptFile);
        }
        if (usePreview) {
            cmdline.push("--extra-output", previewFile);
        }
        if (hasPico8Dat) {
            cmdline.push("--pico8-dat", pico8Dat); // won't hurt to always pass - only read if needed
        }
        if (extraNames) {
            for (let i = 0; i < extraNames.length; i++) {
                let extraInputFile = extraInputFileTmpl.replace("#", i);
                cmdline.push("--extra-input", extraInputFile, "p8", extraNames[i]);
            }
        }

        let [code, stdout] = shrinko8(cmdline);

        let output, preview;
        if (code == 0) {
            if (doZip) {
                makeArchive(outputFile, "zip", outputDir, ".")
            }
            if (encoding) {
                output = fs.readFile(outputFile, {encoding});
            }
            if (usePreview) {
                preview = fs.readFile(previewFile, {encoding: "utf8"});
            }
        }

        return [code, stdout, output, preview];
    },

    runTests: async (argsStr, save) => {
        await initPromise;
        
        if (!self.shrinko8_run_tests) {
            let response = await fetch("shrinko8_test.zip");
            await pyodide.unpackArchive(await response.arrayBuffer(), "zip");

            self.shrinko8_run_tests_args = [];
            if (argsStr) {
                self.shrinko8_run_tests_args.push(...shlex(argsStr))
            }
            if (fs.analyzePath("private_pico_8").exists) {
                self.shrinko8_run_tests_args.push("-p", "private_pico_8/pico8.exe", "-P");
            }

            let run_tests = pyodide.pyimport("run_tests")
            self.shrinko8_run_tests = run_tests.main
        }

        let [exitcode, output] = run_main(self.shrinko8_run_tests, self.shrinko8_run_tests_args);

        let saveData = undefined
        if (save) {
            if (fs.analyzePath("private_test_output").exists) {
                fs.rename("private_test_output", "test_output/private")
            }

            makeArchive("save.zip", "zip", "test_output", ".");
            saveData = fs.readFile("save.zip");
        }

        return [exitcode, output, saveData]
    },
}

Comlink.expose(api);
