var positioner = document.getElementById("top_slow_positioner");
var table = positioner.nextElementSibling;
var anchors = table.getElementsByTagName("a");
var sample = table.nextElementSibling.getElementsByTagName("code")[0];
hljs.highlightElement(sample);
var highlighted = -1;
for (var i = 0; i < anchors.length; i++) {
    anchors[i].addEventListener("click", function(event) {
        event.preventDefault();
        var index = this.getAttribute("href").substring(1);
        row = data[index];
        if (highlighted == index) {
            sample.textContent = "// Click query hash to display sample query...";
            highlighted = -1;
        } else {
            sample.textContent = JSON.stringify(row.sample, null, 2);
            highlighted = index;            
        }
        delete sample.dataset.highlighted;
        hljs.highlightElement(sample);
        sample.scrollIntoView({behavior: "smooth"});
    });
}