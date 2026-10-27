/* KAWSAY AI: diagnostic de arranque. No recoge credenciales ni datos personales. */
(function () {
  var failed = false;
  function markFailure(message) {
    if (failed) return;
    failed = true;
    function show() {
      var root = document.getElementById("root");
      if (!root) return;
      var fallback = document.getElementById("kawsay-fallback");
      if (fallback) {
        var p = document.createElement("p");
        p.setAttribute("role", "alert");
        p.style.color = "#b43636";
        p.style.marginTop = "16px";
        p.textContent = message;
        var card = fallback.querySelector("section") || fallback;
        card.appendChild(p);
      } else if (!root.firstElementChild) {
        root.textContent = "KAWSAY AI: no se pudo iniciar la interfaz. Recarga la página.";
      }
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", show, {once: true});
    else show();
  }
  window.addEventListener("error", function (event) {
    var target = event.target;
    if (target && (target.tagName === "SCRIPT" || target.tagName === "LINK")) {
      markFailure("No se pudo descargar un recurso de la interfaz. Comprueba la conexión y recarga la página.");
    } else if (event.error) {
      console.error("KAWSAY AI: error de inicio de la aplicación", event.error);
      markFailure("Se produjo un error al iniciar el frontend. Abre F12 → Console para ver el detalle.");
    }
  }, true);
  window.addEventListener("unhandledrejection", function (event) {
    console.error("KAWSAY AI: error asíncrono", event.reason);
    markFailure("No se pudo completar el arranque de la aplicación.");
  });
})();
