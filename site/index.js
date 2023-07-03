
let isLoading = true;

// Show shrinko8 loading
function showLoading() {
    isLoading = true;
    $("#loading-overlay").show();

    function updateProgress() {
        api.getProgress().then (progress =>
        {
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

// Called when user loads an input file
function loadInputFile(input) {
    let file = input.files[0];
    if (file) {
        inputMgr.cancel();
        $("#input-error-overlay").hide();
        $("#input-overlay").show();
        let reader = new FileReader();
        function onerror (text) {
            $("#input-overlay").hide();
            $("#input-error-overlay").show();
            applyErrors(-1, text, "#input-error-output");
        }
        reader.onload = async () => {
            try {
                let code = await api.loadInputFile(reader.result, input.value);
                inputMgr.setValue(code); // calls onInputChange
                $("#input-overlay").hide();
                doShrinkoAction();
            } catch (e) {
                console.error(e);
                onerror(e.message);
            }
        };
        reader.onerror = () => {
            onerror("Failed uploading file");
        }
        reader.readAsArrayBuffer(file)
    }
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

// download the output file
async function saveOutputFile() {
    let format = $("#minify-format").val();
    let output = outputMap[format];

    let ext = format;
    if (ext == "tiny-rom") {
        ext = "rom";
    }

    let files = $("#input-code").prop("files");
    let name = (files && files[0]) ? files[0].name : "";
    if (!name) {
        name = "output";
    }

    let type;
    if (isFormatText(format)) {
        type = "text/plain";
    } else if (isFormatImg(format)) {
        type = "image/png";
    } else {
        type = "application/octet-stream";
    }

    download(output, name + "." + ext, type);
}

function isFormatText(fmt) {
    return fmt == "lua" || fmt == "p8";
}
function isFormatImg(fmt) {
    return fmt == "png";
}

async function doShrinko(args, encoding) {
    let argStr = $("#extra-args").val();

    await inputMgr.flush();
    await scriptMgr.flush();

    let useScript = Boolean(scriptMgr.getValue());

    try {
        return await api.runShrinko(args, argStr, useScript, encoding);
    } catch (e) {
        return [-1, e.message, undefined, undefined]
    }
}

function applyErrors(code, stdouterr, selector) {
    let elem = $(selector);
    elem.css("color", code == 0 ? "green" : code == 2 ? "darkgoldenrod" : "red");

    if (code == 0) {
        stdouterr += "Lint succesful - no issues found.";
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
            counts[tokens[2]] = tokens[3]

            let percent = tokens[3] / tokens[4] * 100;
            percents[tokens[2]] = percent.toFixed(percent >= 95 ? 2 : 0) + "%";
        } else {
            rest.push(line);
        }
    }
    
    for (let count of ["tokens", "chars", "compressed"]) {
        $("#count-" + count).text(counts[count]);
        $("#percent-" + count).text(percents[count]);
    }

    return rest.join("\n");
}

let activeMinifies = 0;

async function doMinify() {
    $("#minify-overlay").show();
    activeMinifies++;

    try {
        let args = ["--count", "--parsable-count", "--no-count-compress"]

        let format = $("#minify-format").val();
        args.push("--format", format);

        let minify = $('input[name="minify"]:checked').val();
        if (minify) {
            args.push(...minify.split(" "));
        }

        let focus = $("#minify-focus").val();
        if (focus) {
            args.push(focus);
        }

        let encoding = isFormatText(format) ? "utf8" : "binary";
        let [code, stdouterr, output, preview] = await doShrinko(args, encoding);

        stdouterr = applyCounts(stdouterr);

        if (code != 0) {
            applyErrors(code, stdouterr, "#minify-error-output");
        } else {
            if (isFormatText(format)) {
                $("#minify-code").data("editor").setValue(output, -1);
            } else {
                if (isFormatImg(format)) {
                    setImageUrl("#minify-image", output);
                }
                $("#minify-preview").data("editor").setValue(preview, -1);
            }
        }

        outputMap[format] = code != 0 ? false : output;
        $("#minify-error-overlay").toggle(code != 0);
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
        let args = ["--lint", "--no-lint-fail"];

        if (!$("#lint-undef").prop("checked")) {
            args.push("--no-lint-undefined");
        }
        if (!$("#lint-dup").prop("checked")) {
            args.push("--no-lint-duplicate");
        }
        if (!$("#lint-unused").prop("checked")) {
            args.push("--no-lint-unused");
        }

        let [code, stdouterr, _output, _preview] = await doShrinko(args);

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
    let aggressive = $("#minify-agg").prop("checked");
    $("#minify-max-warn").toggle(aggressive);
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
    $("#minify-binary-div").toggle(!isFormatText(format));
    $("#minify-image").toggle(isFormatImg(format));
    $("#row-compressed").toggle(!isFormatText(format));
    $("#no-row-compressed").toggle(isFormatText(format));
    $("#minify-error-overlay").toggle(outputMap[format] == false);
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

// set up an ace textbox
function setUpAce(id, lang, cb) {
    let editor = ace.edit(id.substring(1))
    editor.session.setMode("ace/mode/" + lang)
    editor.setOptions({
        printMargin: false,
        useWorker: false, // don't check syntax (maybe ok for python)
        readOnly: Boolean($(id).attr("readonly")),
        placeholder: $(id).attr("placeholder"),
    });
    $(id).data("editor", editor);
    if (cb) {
        editor.session.on("change", cb);
    }
}

$(() => {
    api = Comlink.wrap(new Worker("worker.js"));

    showLoading();
    setUpAce("#input-code", "lua", onInputChange);
    setUpAce("#minify-code", "lua");
    setUpAce("#minify-preview", "lua");
    setUpAce("#script-code", "python", onScriptChange);
    $("#output-tabs").tabs({
        activate: onTabChange,
    });

    // (we call below functions with an undefined event, thus avoiding doShrinkoAction being called here)
    $("#minify-opts").change(onMinifyOptsChange); onMinifyOptsChange();
    $("#minify-format").change(onMinifyFormatChange); onMinifyFormatChange();
    $("#lint-opts").change(onLintOptsChange); onLintOptsChange();
    $("#extra-args").change(OnExtraArgsChange);
    
    if (new URLSearchParams(location.search).get("test")) {
        api.runTests().then(alert).catch(alert);
    }
})
