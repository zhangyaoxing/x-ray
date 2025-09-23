var positioner = document.getElementById("top_slow_positioner");
var table = positioner.nextElementSibling;
var anchors = table.getElementsByTagName("a");
var sample = table.nextElementSibling.getElementsByTagName("code")[0];
var highlighted = -1;
for (var i = 0; i < anchors.length; i++) {
    anchors[i].addEventListener("click", function(event) {
        event.preventDefault();
        var index = this.getAttribute("href").substring(1);
        row = data[index];
        if (highlighted == index) {
            highlighted = -1;
            sample.textContent = "// Click query hash to display sample slow query...";
            return
        }
        sample.textContent = JSON.stringify(row.sample, null, 2);
        delete sample.dataset.highlighted;
        hljs.highlightElement(sample);
        highlighted = index;
    });
}