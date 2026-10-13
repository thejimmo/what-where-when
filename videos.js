// Fills the "Latest episode" and "Latest Shorts" sections from data/videos.json,
// which a scheduled GitHub Action refreshes from the channel's RSS feed.
(function () {
  var thumb = function (id, size) { return "https://i.ytimg.com/vi/" + id + "/" + size + ".jpg"; };

  function el(tag, props) {
    var node = document.createElement(tag);
    for (var k in props) node[k] = props[k];
    return node;
  }

  // Show a thumbnail and only load YouTube's player once the visitor presses play.
  function showLatest(video) {
    var section = document.getElementById("latest");
    var player = section.querySelector(".player");
    var button = el("button", { type: "button", className: "play" });
    button.setAttribute("aria-label", "Play " + video.title);
    var img = el("img", { src: thumb(video.id, "maxresdefault"), alt: "", loading: "lazy" });
    img.onerror = function () { img.onerror = null; img.src = thumb(video.id, "hqdefault"); };
    button.append(img, el("span", { className: "play-icon" }));
    button.addEventListener("click", function () {
      var frame = el("iframe", {
        src: "https://www.youtube-nocookie.com/embed/" + video.id + "?autoplay=1&rel=0",
        title: video.title,
        allowFullscreen: true
      });
      frame.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
      player.replaceChildren(frame);
      frame.focus();
    });
    player.append(button);
    section.querySelector(".latest-title").textContent = video.title;
    section.hidden = false;
  }

  function showShorts(shorts) {
    var section = document.getElementById("shorts");
    var row = section.querySelector(".shorts-row");
    shorts.forEach(function (video) {
      var link = el("a", { href: "https://www.youtube.com/shorts/" + video.id });
      link.append(
        el("img", { src: thumb(video.id, "hqdefault"), alt: "", loading: "lazy" }),
        el("span", { textContent: video.title })
      );
      var item = el("li");
      item.append(link);
      row.append(item);
    });
    section.querySelectorAll(".row-nav button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        row.scrollBy({ left: Number(btn.dataset.dir) * row.clientWidth * 0.9, behavior: "smooth" });
      });
    });
    section.hidden = false;
  }

  fetch("data/videos.json")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (data) {
      if (!data) return;
      if (data.longform && data.longform.length) showLatest(data.longform[0]);
      if (data.shorts && data.shorts.length) showShorts(data.shorts);
    })
    .catch(function () {});
})();
