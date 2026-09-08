/* Shared inline-code copy-to-clipboard feature.
 *
 * Every backtick-wrapped string (rendered by markdown as an inline <code>,
 * i.e. not inside a <pre> block) gets a small copy button that appears next
 * to it on hover. Clicking the button copies the string to the clipboard.
 */

function inlineCodeCopySetup() {
    var codes = document.querySelectorAll("code");
    codes.forEach(function (code) {
        if (code.classList.contains("code-copyable")) return;
        // Skip code blocks (handled by highlightjs-copy) and our own chrome.
        if (code.closest("pre") || code.closest(".risk-tooltip") || code.closest(".code-copy-btn")) return;
        code.classList.add("code-copyable");

        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "code-copy-btn";
        btn.setAttribute("aria-label", "Copy code");
        btn.title = "Copy";
        btn.innerHTML =
            '<svg viewBox="0 0 16 16" aria-hidden="true">' +
            '<path d="M5 3V1.5A1.5 1.5 0 0 1 6.5 0h6A1.5 1.5 0 0 1 14 1.5v8a1.5 1.5 0 0 1-1.5 1.5H11v-1.5h1.5v-8h-6V3H5Z"/>' +
            '<path d="M2 6.5A1.5 1.5 0 0 1 3.5 5h6A1.5 1.5 0 0 1 11 6.5v8A1.5 1.5 0 0 1 9.5 16h-6A1.5 1.5 0 0 1 2 14.5v-8Z"/></svg>';

        btn.addEventListener("click", function () {
            var text = code.textContent || "";
            var onDone = function () {
                btn.classList.add("code-copied");
                btn.title = "Copied";
                setTimeout(function () {
                    btn.classList.remove("code-copied");
                    btn.title = "Copy";
                }, 1500);
            };
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(onDone, function () { fallbackCopyText(text, onDone); });
            } else {
                fallbackCopyText(text, onDone);
            }
        });

        code.appendChild(btn);
    });
}

function fallbackCopyText(text, onDone) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
        document.execCommand("copy");
        onDone();
    } catch (e) { /* ignore */ }
    document.body.removeChild(ta);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inlineCodeCopySetup);
} else {
    inlineCodeCopySetup();
}
