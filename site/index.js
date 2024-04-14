'use strict';

$.fn.extend({
    isShown: function() { return this.css("display") != "none"; },
    isChecked: function() { return this.prop("checked"); },
})

let isLoading = true;

// Show shrinko8 loading
function showLoading() {
    isLoading = true;
    $("#loading-overlay").show();

    function updateProgress() {
        api.getProgress().then(progress => {
            console.log(progress);
            if (progress < 0) {
                $("#loading-failed").show();
            } else if (progress >= 100) {
                $("#loading-overlay").hide();
                isLoading = false;
                doShrinkoAction(); // initial
            } else {
                $("#loading-progress").val(progress);
                setTimeout(updateProgress, 100);
            }
        });
    }

    updateProgress();
}

// Show shrinko8 version
function showVersion() {
    api.getVersion().then(version => {
        $("#version").text(version);
    }).catch(e => {
        $("#version").text("v???");
    });
}

// Give a download to the user
function download(data, filename, type) {
    let blob = new Blob([data], {type});
    let url = URL.createObjectURL(blob);
    let a = document.createElement("a");
    a.download = filename
    a.href = url
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

class InputChangeMgr {
    constructor(selector, updateApiName) {
        this.selector = selector;
        this.updateApiName = updateApiName;
        this.pending = undefined;
        this.promise = undefined;
        this.inProg = false;

        this.fileName = "";
        this.extraNames = [];
    }

    // Cancel any pending input changes
    cancel() {
        if (this.pending !== undefined) {
            clearTimeout(this.pending);
            this.pending = undefined;
            return true;
        }
    }

    // Flush any input changes, returns a promise to wait for
    flush() {
        if (this.cancel()) {
            let updateApi = api[this.updateApiName];
            this.promise = updateApi(this.getValue());
        }
        return this.promise;
    }
    
    onChange(cb) {
        if (!this.inProg) {
            this.cancel();
            this.pending = setTimeout(async () => {
                await this.flush();
                if (cb) {
                    cb();
                }
            }, 500);
        }
    }

    editor() {
        return $(this.selector).data("editor");
    }

    getValue() {
        return this.editor().getValue();
    }

    setValue(code) {
        this.inProg = true;
        this.editor().setValue(code, -1);
        this.inProg = false;
    }
}

let inputMgr = new InputChangeMgr("#input-code", "updateInputFile");
let outputMap = {};

// Called when the input value changes
function onInputChange(delta) {
    outputMap = {}
    inputMgr.onChange(doShrinkoAction);
}

// returns a promise that's resolved when the File is read
function readFile(file) {
    return new Promise((resolve, reject) => {
        let reader = new FileReader();
        reader.onload = async () => {
            resolve(reader.result);
        };
        reader.onerror = () => {
            reject(new Error("Read failed"));
        }
        reader.readAsArrayBuffer(file)
    })
}

// returns all files (& their parent paths) in a fs entry
async function readFSEntryRec(entry, relpath, results) {
    if (entry.isDirectory) {
        let dirpath = joinPath(relpath, entry.name);
        let reader = entry.createReader();
        while (true) {
            let entries = await new Promise((r,j) => reader.readEntries(r,j));
            if (entries.length == 0) {
                break;
            }

            for (let entry of entries) {
                await readFSEntryRec(entry, dirpath, results);
            }
        }
    } else if (entry.isFile) {
        results.push([await new Promise((r,j) => entry.file(r,j)), relpath]);
    }
    return results; // for convenience
}

// Called when user loads an input file
async function loadInputFiles(inputs) {
    if (inputs.length == 0) {
        return;
    }

    inputMgr.cancel();
    $("#input-error-overlay").hide();
    $("#input-select-overlay").hide();
    $("#input-overlay").show();
    
    function onerror(text) {
        $("#input-overlay").hide();
        $("#input-error-overlay").show();
        applyErrors(-1, text, "#input-error-output");
    }

    let allFiles = new Map();
    let firstP8 = undefined;
    async function processFile(file, relpath) {
        try {
            let path = joinPath(relpath, file.name);
            let data = await readFile(file);
            allFiles.set(path, data);

            if (getLowExt(file.name) == "p8") {
                if (firstP8 == undefined) {
                    firstP8 = path;
                }
            }
        } catch (e) {
            onerror(`Failed reading ${file.name} from your local machine`);
            throw e;
        }
    }

    // handle the files in parallel, as some browsers will not allow otherwise
    await Promise.all(Array.prototype.map.call(inputs, async input => {
        if (input instanceof DataTransferItem) {
            let content;
            let asEntry = input.webkitGetAsEntry || input.getAsEntry;
            if (asEntry) {
                content = asEntry.call(input);
            }

            if (!content) {
                content = input.getAsFile();
            }
            input = content;
        }

        if (input instanceof File) {
            await processFile(input, "");
        } else { // no fixed class name, assume it's a FileSystemEntry
            for (let [file, relpath] of await readFSEntryRec(input, "", [])) {
                await processFile(file, relpath);
            }
        }
    }));

    let mainPath, extraPaths;
    if (allFiles.size == 0) {
        onerror("Failed reading any files from your local machine");
        return;
    } else if (allFiles.size == 1) {
        mainPath = allFiles.keys().next().value;
    } else {
        [mainPath, extraPaths] = await beginInputSelect(allFiles.keys(), "main", firstP8);
    }

    let subfile = undefined;
    if (isFormatExport(getLowExt(mainPath))) {
        let subfiles = await api.listInputFile(allFiles, mainPath);
        if (subfiles.length == 1) {
            subfile = subfiles[0];
        } else {
            [subfile] = await beginInputSelect(subfiles, "export");
        }
    }
    
    try {
        let code = await api.loadInputFiles(allFiles, mainPath, subfile, extraPaths);
        inputMgr.setValue(code); // calls onInputChange

        $("#input-overlay").hide();
        
        inputMgr.fileName = getBaseName(mainPath)
        inputMgr.extraNames = extraPaths ? extraPaths.map(getBaseName) : [];
        let numExtras = inputMgr.extraNames.length;
        $("#input-extra-files").toggle(numExtras > 0);
        $("#input-extra-count").text(numExtras);

        doShrinkoAction();
    } catch (e) {
        console.error(e);
        onerror(e.message);
    }
}

// called when file input selection changed
function loadSelectedFiles(input) {
    let entries = input.webkitEntries;
    if (entries && entries.length > 0) {
        loadInputFiles(entries);
    } else {
        loadInputFiles(input.files);
    }
}

// are we dragging a file?
function isFileDrag(event) {
    let items = event.dataTransfer.items;
    for (let item of items) {
        if (item.kind != "file") {
            return false;
        }
    }
    return true;
}

function getDragTarget(elem) {
    let jqelem = $(elem);
    let selector = jqelem.data("droptarget");
    if (selector) {
        jqelem = $(selector);
    }
    return jqelem;
}

function onDragEnter(elem, event) {
    if (isFileDrag(event)) {
        event.preventDefault();
        event.dataTransfer.dropEffect = "copy";
        getDragTarget(elem).addClass("dragover");
    }
}

function onDragLeave(elem, event) {
    if (isFileDrag(event)) {
        getDragTarget(elem).removeClass("dragover");
    }
}

function onDrop(elem, event, type) {
    if (isFileDrag(event)) {
        event.preventDefault();
        onDragLeave(elem, event);
        if (type == "input") {
            loadInputFiles(event.dataTransfer.items);
        }
    }
}

// called to close the input error overlay
function onInputErrorClose() {
    $('#input-error-overlay').hide();
}

let inputSelectResolve;

// create ui to select a file, return promise for the ui's end (may never resolve)
async function beginInputSelect(paths, reason, initialSel) {
    $('#input-select-overlay').show();
    $("#input-overlay").hide();
    
    $("#input-select-main-label").toggle(reason == "main")
    $("#input-select-export-label").toggle(reason == "export")

    let inExtraMode = false;
    $("#input-select-extra-label").toggle(reason == "main");
    let selectExtra = $("#input-select-extra");
    selectExtra.prop("checked", false);
    selectExtra.click(() => {
        inExtraMode = !inExtraMode;
    })

    let elem = $('#input-select-list');
    elem.empty();

    let selDiv;
    let extraSelDivs = [];
    for (let path of paths) {
        let div = $("<div/>");
        div.text(path);
        div.css("cursor", "pointer");

        div.click(() => {
            if (inExtraMode) {
                if (div !== selDiv) {
                    if (extraSelDivs.includes(div)) {
                        extraSelDivs = extraSelDivs.filter(item => item !== div);
                        div.removeClass("extra-selected");
                    } else {
                        extraSelDivs.push(div);
                        div.addClass("extra-selected");
                    }
                }
            } else {
                if (!extraSelDivs.includes(div)) {
                    if (selDiv) {
                        selDiv.removeClass("selected");
                    }
                    div.addClass("selected");
                    selDiv = div;
                }
            }
        });
        
        if (!selDiv && (path === initialSel || !initialSel)) {
            selDiv = div;
            selDiv.click();
        }

        elem.append(div);
    }

    await new Promise((resolve) => {
        inputSelectResolve = resolve;
    });
    
    $('#input-select-overlay').hide();
    $("#input-overlay").show();

    let extraSels;
    if (extraSelDivs.length) {
        extraSels = extraSelDivs.map(div => div.text());
    }

    return [selDiv.text(), extraSels];
}

// called to finish selecting a file
function onInputSelect() {
    inputSelectResolve();
}

function onInputSelectClose() {
    $('#input-select-overlay').hide();
}

let hasPico8Dat = false;

async function loadPico8Dat(file) {
    let data = await readFile(file);
    await api.updatePico8Dat(data);
    
    hasPico8Dat = true;
    $("#minify-pico8dat-overlay").hide();
    outputMap = {}
    doShrinkoAction();
}

let scriptMgr = new InputChangeMgr("#script-code", "updateScriptFile");

// Called when the script value changes
function onScriptChange(delta) {
    scriptMgr.onChange();
    outputMap = {}
}

// Called when the extra args changes (called in advanced tab, no need to update immediately)
function OnExtraArgsChange() {
    outputMap = {}
}

// set the url of the image from data bytes
function setImageUrl(selector, data) {
    let blob = new Blob([data]);
    let url = URL.createObjectURL(blob);
    let img = $(selector).get(0);
    img.src = url;
    img.onload = () => {
        URL.revokeObjectURL(url);
    }
}

// copy the edu url to clipboard
function copyUrlToClipboard() {
    navigator.clipboard.writeText($("#minify-url").attr("href"));
    $("#minify-url-copied").show();
}

// download the output file
async function saveOutputFile() {
    let format = $("#minify-format").val();
    let output = outputMap[format];

    let ext = format;
    if (ext == "tiny-rom") {
        ext = "rom";
    }
    if (ext == "png" || ext == "rom") {
        ext = "p8." + ext;
    }

    let name = getWithoutAllExts(inputMgr.fileName);
    if (!name) {
        name = "output";
    }

    let type;
    if (isFormatText(format)) {
        type = "text/plain";
    } else if (isFormatImg(format)) {
        type = "image/png";
    } else if (isFormatNeedZip(format)) {
        type = "application/zip"
        ext = "zip"
    } else {
        type = "application/octet-stream";
    }

    download(output, name + "." + ext, type);
}

async function doShrinko(args, encoding, usePreview, doZip, extraNames) {
    let argStr = $("#extra-args").val();

    await inputMgr.flush();
    await scriptMgr.flush();

    let useScript = Boolean(scriptMgr.getValue());

    try {
        return await api.runShrinko(args, argStr, useScript, encoding, usePreview, doZip, extraNames);
    } catch (e) {
        console.error(e);
        return [-1, e.message, undefined, undefined]
    }
}

function applyErrors(code, stdouterr, selector) {
    let elem = $(selector);
    elem.css("color", code == 0 ? "green" : code == 2 ? "darkgoldenrod" : "red");

    if (code == 0) {
        stdouterr += "Lint succesful - no issues found.";
    }

    if (stdouterr.match(/^.*cannot open included cart/i)) {
        stdouterr += "\nTo fix this, select (or drop) both the main p8 file and all its includes.";
        stdouterr += "\nIf your includes are inside subfolders, you can drag & drop the whole parent directory to the input area.";
    }

    elem.empty();
    for (let line of stdouterr.split("\n")) {
        let span = $("<span/>");

        let fields = line.split(":");
        if (fields.length >= 4 && !isNaN(fields[1]) && !isNaN(fields[2])) {
            span.text(fields.slice(3).join(":"));
            let link = $('<a href="#" />');
            link.text(fields.slice(0, 3).join(":"));
            link.click(() => {
                let row = fields[1] - 1;
                let col = fields[2] - 1;
                inputMgr.editor().selection.moveTo(row, col);
                inputMgr.editor().scrollToLine(row, true);
            });
            span.prepend(link);
        } else {
            span.text(line);
        }

        elem.append(span, $("<br/>"));
    }
}

function applyCounts(stdouterr) {
    let rest = [];

    let counts = {}, percents = {};
    for (let line of stdouterr.split("\n")) {
        let tokens = line.trim().split(":");
        if (tokens.length >= 5 && tokens[0] == "count") {
            let type = tokens[2];
            if (!counts[type]) {
                counts[type] = tokens[3]

                let percent = tokens[3] / tokens[4] * 100;
                percents[type] = percent.toFixed(percent >= 95 ? 2 : 0) + "%";
            }
        } else {
            rest.push(line);
        }
    }
    
    for (let count of ["tokens", "chars", "compressed", "url"]) {
        $("#count-" + count).text(counts[count]);
        $("#percent-" + count).text(percents[count]);
    }

    return rest.join("\n");
}

let activeMinifies = 0;

async function doMinify() {
    $("#minify-diag-output").hide();
    $("#minify-overlay").show();
    activeMinifies++;

    try {
        // people are likely to copy stuff from the output/preview, so --unicode-caps helps there
        // (they're legal in p8 files, so shouldn't be a problem)
        let args = ["--count", "--parsable-count", "--no-count-compress", "--unicode-caps"]

        let format = $("#minify-format").val();
        args.push("--format", format);

        let minify = $('input[name="minify"]:checked').val();
        if (minify) {
            args.push(...minify.split(" "));
        }

        let focus = $("#minify-focus").val();
        if (focus) {
            args.push(...focus.split(" "));
        }

        if ($("#minify-max-table").isShown()) {
            if (!$("#minify-rename-max").isChecked()) {
                args.push("--rename-safe-only");
            }
            if (!$("#minify-reorder-max").isChecked()) {
                args.push("--reorder-safe-only");
            }
        }

        if ($("#minify-keep-lines").isChecked()) {
            args.push("--no-minify-lines");
        }

        // (adjust p8 preview)
        if (format === "tiny-rom") {
            args.push("--output-sections", "lua");
        } else if (format === "url") {
            args.push("--output-sections", "lua,gfx");
        }

        if (isFormatExport(format)) {
            args.push("--export-name", getWithoutAllExts(inputMgr.fileName));
            args.push("--output-cart", inputMgr.fileName);
        }

        let encoding = isFormatText(format) || isFormatUrl(format) ? "utf8" : "binary";
        let usePreview = !isFormatText(format);
        let doZip = isFormatNeedZip(format);
        let extraNames = isFormatExport(format) ? inputMgr.extraNames : undefined;

        let [code, stdouterr, output, preview] = await doShrinko(args, encoding, usePreview, doZip, extraNames);

        stdouterr = applyCounts(stdouterr);

        if (code != 0) {
            applyErrors(code, stdouterr, "#minify-error-output");
        } else {
            if (isFormatText(format)) {
                $("#minify-code").data("editor").setValue(output, -1);
            } else if (isFormatUrl(format)) {
                $("#minify-url").attr("href", output).text(output);
                $("#minify-url-preview").data("editor").setValue(preview, -1);
                $("#minify-url-copied").hide();
            } else {
                if (isFormatImg(format)) {
                    setImageUrl("#minify-image", output);
                }
                $("#minify-preview").data("editor").setValue(preview, -1);
            }
            
            applyErrors(2, stdouterr, "#minify-diag-output");
        }

        outputMap[format] = code != 0 ? false : output;
        $("#minify-error-overlay").toggle(code != 0);
        $("#minify-diag-output").toggle(code == 0 && stdouterr !== "");
    } finally {
        if (--activeMinifies == 0) {
            $("#minify-overlay").hide();
        }
    }
}

let activeLints = 0;

async function doLint() {
    $("#lint-overlay").show();
    activeLints++;
    
    try {
        let args = ["--lint"];

        if (!$("#lint-undef").isChecked()) {
            args.push("--no-lint-undefined");
        }
        if (!$("#lint-dup").isChecked()) {
            args.push("--no-lint-duplicate");
        }
        if (!$("#lint-unused").isChecked()) {
            args.push("--no-lint-unused");
        }

        let [code, stdouterr] = await doShrinko(args);

        applyErrors(code, stdouterr, "#lint-output");

        outputMap.lint = true;
    } finally {
        if (--activeLints == 0) {
            $("#lint-overlay").hide();
        }
    }
}

// do the shrinko action for the current tab. returns awaitable
function doShrinkoAction() {
    if (isLoading) {
        return; // not yet
    }

    let activeTab = $("#output-tabs").tabs("option", "active");
    switch (activeTab) {
        case 0: { // minify
            let format = $("#minify-format").val();
            if (!(format in outputMap)) {
                outputMap[format] = null;
                return doMinify();
            }
            break;
        } case 1: { // lint
            if (!("lint" in outputMap)) {
                outputMap.lint = null;
                return doLint();
            }
            break;
        }
    }
}

// called when the minify options change
function onMinifyOptsChange(event) {
    let aggressive = $("#minify-agg").isChecked();
    $("#minify-max-div").toggle(aggressive);

    let needTable = $("#minify-focus").val().includes("--focus-tokens");
    $("#minify-max-table").toggle(aggressive && needTable);

    if (event) {
        $("#minify-format option").each(function () {
            delete outputMap[this.value];
        });
        doShrinkoAction();
    }
}

// called when the minify output format changes
function onMinifyFormatChange(event) {
    let format = $("#minify-format").prop("value");
    $("#minify-text-div").toggle(isFormatText(format));
    $("#minify-url-div").toggle(isFormatUrl(format));
    $("#minify-binary-div").toggle(!isFormatText(format) && !isFormatUrl(format));
    $("#minify-image").toggle(isFormatImg(format));
    $("#file-icon").toggle(!isFormatImg(format));
    $("#row-compressed").toggle(!isFormatText(format) && !isFormatUrl(format));
    $("#row-url-compressed").toggle(isFormatUrl(format));
    $("#no-row-compressed").toggle(isFormatText(format));
    $("#minify-error-overlay").toggle(outputMap[format] === false);
    $("#minify-pico8dat-overlay").toggle(isFormatExport(format) && !hasPico8Dat);

    if (isFormatText(format)) {
        initAceIfNeeded("#minify-code", "lua");
    } else if (isFormatUrl(format)) {
        initAceIfNeeded("#minify-url-preview", "lua");
    } else {
        initAceIfNeeded("#minify-preview", "lua");
    }

    if (event) {
        doShrinkoAction();
    }
}

// called when the lint options change
function onLintOptsChange(event) {
    if (event) {
        delete outputMap.lint;
        doShrinkoAction();
    }
}

// called when the tab changes
function onTabChange() {
    if (isLoading) {
        let activeTab = $("#output-tabs").tabs("option", "active");
        switch (activeTab) {
            case 0: {
                $("#loading-overlay").appendTo("#minify-overlay-parent");
                break;
            } case 1: {
                $("#loading-overlay").appendTo("#lint-overlay-parent");
                break;
            }
        }
    }
    doShrinkoAction();
}

// set up an ace textbox, unless already done
function initAceIfNeeded(id, lang, cb) {
    let elem = $(id);
    if (!elem.data("editor")) {
        let editor = ace.edit(id.substring(1))
        editor.session.setMode("ace/mode/" + lang)
        editor.setOptions({
            printMargin: false,
            useWorker: false, // don't check syntax (maybe ok for python)
            readOnly: Boolean(elem.attr("readonly")),
            placeholder: elem.attr("placeholder"),
        });
        elem.data("editor", editor);
        if (cb) {
            editor.session.on("change", cb);
        }
    }
}

async function runTests(mode, argsStr) {
    async function endTest(ok, msg, save) {
        if (mode == "post") {
            await fetch(ok ? "test-ok" : "test-fail", {
                method: "post",
                headers: {"content-type": "text/plain"},
                body: msg,
            })
            window.close();
        } else {
            alert(msg);
            if (save) {
                download(save, "save.zip", "application/zip");
            }
        }
    }

    try {
        let [status, output, save] = await api.runTests(argsStr, mode == "save")
        endTest(status == 0, output, save)
    } catch (e) {
        console.error(e);
        endTest(false, e.message)
    }
}

$(() => {
    self.api = Comlink.wrap(new Worker("worker.js"));

    showLoading();
    showVersion();
    initAceIfNeeded("#input-code", "lua", onInputChange);
    initAceIfNeeded("#script-code", "python", onScriptChange);
    $("#output-tabs").tabs({activate: onTabChange});

    // (we call below functions with an undefined event, thus avoiding doShrinkoAction being called here)
    $("#minify-opts").change(onMinifyOptsChange); onMinifyOptsChange();
    $("#minify-format").change(onMinifyFormatChange); onMinifyFormatChange();
    $("#lint-opts").change(onLintOptsChange); onLintOptsChange();
    $("#extra-args").change(OnExtraArgsChange);
    
    let params = new URLSearchParams(location.search);
    let testMode = params.get("test");
    if (testMode) {
        runTests(testMode, params.get("test-args"))
    }
})
