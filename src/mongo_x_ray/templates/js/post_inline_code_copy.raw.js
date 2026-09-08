/* Shared code copy-to-clipboard feature (issue #334).
 *
 * - Inline code: every backtick-wrapped string (markdown <code>, not inside
 *   <pre>) gets a small copy icon that flows after the text.
 * - Code blocks: the highlightjs-copy button (which renders "Copy" text) is
 *   taken over and restyled to the same icon, top-right of the block.
 * Clicking copies the string and shows a transient ✓ confirmation.
 */

var CODE_COPY_ICON =
    '<svg viewBox="0 0 16 16" aria-hidden="true">' +
    '<path d="M5 3V1.5A1.5 1.5 0 0 1 6.5 0h6A1.5 1.5 0 0 1 14 1.5v8a1.5 1.5 0 0 1-1.5 1.5H11v-1.5h1.5v-8h-6V3H5Z"/>' +
    '<path d="M2 6.5A1.5 1.5 0 0 1 3.5 5h6A1.5 1.5 0 0 1 11 6.5v8A1.5 1.5 0 0 1 9.5 16h-6A1.5 1.5 0 0 1 2 14.5v-8Z"/></svg>';

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

function copyCodeText(text, btn) {
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
}

/* Reconstruct the text of a <pre> block. Report content is often rendered as
 * <br> line breaks and &nbsp; indentation (not literal newlines), so
 * textContent alone would lose the line breaks. */
function preBlockText(pre) {
    var out = "";
    (function walk(node) {
        node.childNodes.forEach(function (c) {
            if (c.nodeType === 3) {
                out += c.nodeValue;
            } else if (c.nodeType === 1) {
                if (c.tagName === "BR") {
                    out += "\n";
                } else {
                    walk(c);
                }
            }
        });
    })(pre);
    return out.replace(/\u00a0/g, " ");
}

/* Inline (backtick) code: add a copy icon inside each <code> element. */
function inlineCodeCopySetup() {
    var codes = document.querySelectorAll("code");
    codes.forEach(function (code) {
        if (code.classList.contains("code-copyable")) return;
        // Skip code blocks (handled below) and our own chrome.
        if (code.closest("pre") || code.closest(".risk-tooltip") || code.closest(".code-copy-btn")) return;
        code.classList.add("code-copyable");

        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "code-copy-btn";
        btn.setAttribute("aria-label", "Copy code");
        btn.title = "Copy";
        btn.innerHTML = CODE_COPY_ICON;
        btn.addEventListener("click", function () { copyCodeText(code.textContent || "", btn); });
        code.appendChild(btn);
    });
}

/* Code blocks: take over the highlightjs-copy button and restyle it as the
 * same icon (top-right of the block) with our own copy behavior, so it never
 * conflicts with the "Copy"/"Copied!" text swapping of the hljs plugin.
 * Bare <pre> blocks (e.g. JSON samples inside tables) that hljs does not
 * manage get the same top-right icon too. */
function blockCodeCopySetup() {
    document.querySelectorAll(".hljs-copy-button").forEach(function (btn) {
        if (btn.dataset.codeCopyUnified) return;
        var wrapper = btn.closest(".hljs-copy-wrapper");
        if (!wrapper) return; // only manage buttons that live in an hljs wrapper
        var code = wrapper.querySelector("pre code") || wrapper.querySelector("code");
        if (!code) {
            btn.remove();
            return;
        }
        // Replace the button to drop the hljs plugin's own click handler.
        var fresh = btn.cloneNode(false);
        btn.parentNode.replaceChild(fresh, btn);
        fresh.dataset.codeCopyUnified = "1";
        fresh.setAttribute("aria-label", "Copy code");
        fresh.title = "Copy";
        fresh.innerHTML = CODE_COPY_ICON;
        fresh.addEventListener("click", function () { copyCodeText(preBlockText(code), fresh); });
    });

    document.querySelectorAll("pre").forEach(function (pre) {
        if (pre.classList.contains("hljs-copy-wrapper") || pre.closest(".risk-tooltip")) return;
        if (pre.dataset.codeCopyUnified) return;
        pre.dataset.codeCopyUnified = "1";
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "hljs-copy-button"; // reuse the block-button styles
        btn.dataset.codeCopyUnified = "1";
        btn.setAttribute("aria-label", "Copy code");
        btn.title = "Copy";
        btn.innerHTML = CODE_COPY_ICON;
        btn.addEventListener("click", function () { copyCodeText(preBlockText(pre), btn); });
        pre.appendChild(btn);
    });
}

/* Inline (backtick) code can be set up immediately; the block/bare-<pre>
 * buttons wait until the report scripts (hljs highlighting, dynamic tables)
 * have finished so nothing overwrites them afterwards. */
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inlineCodeCopySetup);
} else {
    inlineCodeCopySetup();
}
function lateBlockSetup() { blockCodeCopySetup(); }
window.addEventListener("load", lateBlockSetup);
setTimeout(lateBlockSetup, 400);
setTimeout(lateBlockSetup, 1200);
