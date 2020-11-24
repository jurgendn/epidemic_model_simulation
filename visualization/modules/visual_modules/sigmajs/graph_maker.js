const container = document.getElementById("container");
container.style.width = window.innerWidth + "px";
container.style.height = window.innerHeight + "px";

let searchBox = document.getElementById("searchNode");

let dt;

let s = new sigma({
  renderer: {
    container: document.getElementById("container"),
    type: "canvas",
  },
  settings: {
    defaultEdgeType: "curvedArrow",
    autoRescale: true,
  },
});

fetch("data/data.json")
  .then((response) => response.json())
  .then((data) => {
    s.graph.read(data);

    s.graph.edges().forEach((edge) => {
      edge.color = edge._color;
    });

    s.graph.nodes().forEach((node) => {
      node.color = node._color;
    });

    s.refresh();
  });

// $.ajax({
//   async: false,
//   global: false,
//   url: "data.json",
//   dataType: "json",
//   success: function (dt) {
//     data = dt;
//   },
// });

// s.graph.read(dt);

// s.graph.edges().forEach((edge) => {
//   edge.color = edge._color;
// });

// s.graph.nodes().forEach((node) => {
//   node.color = node._color;
// });

// s.renderers[0].snapshot({ format: "jpg", background: "white", download: true });

// s.refresh();

let dragListener = sigma.plugins.dragNodes(s, s.renderers[0]);

dragListener.bind("startdrag", function (event) {
  console.log(event);
});
dragListener.bind("drag", function (event) {
  console.log(event);
});
dragListener.bind("drop", function (event) {
  console.log(event);
});
dragListener.bind("dragend", function (event) {
  console.log(event);
});

s.bind("overNode", function (n) {
  document.getElementById("p_name").innerText = n.data.node.full_name;
  document.getElementById("p_onset").innerText = n.data.node.onset_date;
  document.getElementById("p_announce").innerText = n.data.node.announce_date;
  document.getElementById("p_rank").innerText = n.data.node.pagerank;
  document.getElementById("p_quarantine").innerText =
    n.data.node.quarantine_date;
});
s.bind("outNode", function (n) {
  document.getElementById("p_name").innerText = "";
  document.getElementById("p_onset").innerText = "";
  document.getElementById("p_announce").innerText = "";
  document.getElementById("p_rank").innerText = "";
  document.getElementById("p_quarantine").innerText = "";
});

// console.log(data);
searchBox.addEventListener("keyup", function (evt) {
  if (evt.key === "Enter") {
    const nodeName = searchBox.value;
    s.graph.nodes().forEach((node) => {
      if (node.label === nodeName) {
        node.color = "#00ff80";
        node.size = 5;
      }
    });
  }
});

var config = {
  node: [
    {
      show: "hovers",
      hide: "hovers",
      cssClass: "sigma-tooltip",
      position: "top",
      //autoadjust: true,
      template:
        '<div class="arrow"></div>' +
        '<div class="sigma-tooltip-header">{{label}}</div>' +
        '<div class="sigma-tooltip-body">' +
        "  <table>" +
        "    <tr><th>Name</th> <td>{{data.fullName}}</td></tr>" +
        "    <tr><th>Onset date</th> <td>{{data.onset_date}}</td></tr>" +
        "    <tr><th>Announce date</th> <td>{{data.announce_date}}</td></tr>" +
        "    <tr><th>Quarantine date</th> <td>{{data.quarantine_date}}</td></tr>" +
        "  </table>" +
        "</div>" +
        '<div class="sigma-tooltip-footer">Rank: {{data.pagerank}} </div>',
      renderer: function (node, template) {
        // The function context is s.graph
        // Returns an HTML string:
        return Mustache.render(template, node);
      },
    },
    {
      show: "overNode",
      cssClass: "sigma-tooltip",
      position: "right",
      template:
        '<div class="arrow"></div>' +
        '<div class="sigma-tooltip-header">{{label}}</div>' +
        '<div class="sigma-tooltip-body">' +
        "  <table>" +
        "    <tr><th>Name</th> <td>{{data.fullName}}</td></tr>" +
        "    <tr><th>Onset date</th> <td>{{data.onset_date}}</td></tr>" +
        "    <tr><th>Announce date</th> <td>{{data.announce_date}}</td></tr>" +
        "    <tr><th>Quarantine date</th> <td>{{data.quarantine_date}}</td></tr>" +
        "  </table>" +
        "</div>" +
        '<div class="sigma-tooltip-footer">Rank: {{data.pagerank}} </div>',
      renderer: function (node, template) {
        return Mustache.render(template, node);
      },
    },
  ],
  stage: {
    template:
      '<div class="arrow"></div>' +
      '<div class="sigma-tooltip-header"> Menu </div>',
  },
};

var tooltips = sigma.plugins.tooltips(s, s.renderers[0], config);

tooltips.bind("shown", function (event) {
  //console.log('tooltip shown');
});

tooltips.bind("hidden", function (event) {
  //console.log('tooltip hidden');
});
