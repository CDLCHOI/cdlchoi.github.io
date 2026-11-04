(function() {
  'use strict';

  var widget = document.querySelector('[data-supercounters-flag]');
  if (!widget) return;

  var status = widget.querySelector('[data-supercounters-status]');
  var retry = widget.querySelector('[data-supercounters-retry]');
  var library;
  var timeout;
  var libraryRetries = 0;

  function rendered() {
    var counters = widget.querySelectorAll('[title="Flag Counter"]');
    if (!counters.length) return false;
    // A slow response from an earlier attempt must not duplicate the widget.
    Array.from(counters).slice(1).forEach(function(counter) { counter.remove(); });
    window.clearTimeout(timeout);
    status.hidden = true;
    retry.hidden = true;
    return true;
  }

  function failed() {
    if (rendered()) return;
    window.clearTimeout(timeout);
    status.textContent = 'Visitor statistics could not load.';
    retry.hidden = false;
  }

  function load() {
    if (rendered()) return;
    window.clearTimeout(timeout);
    status.hidden = false;
    status.textContent = 'Loading visitor statistics…';
    retry.hidden = true;
    if (library) library.remove();

    var script = document.createElement('script');
    library = script;
    script.src = 'https://widget.supercounters.com/ssl/flag.js';
    script.async = true;
    script.onerror = function() {
      if (library !== script || rendered()) return;
      window.clearTimeout(timeout);
      if (libraryRetries < 1) {
        libraryRetries += 1;
        window.setTimeout(load, 1500);
      } else {
        failed();
      }
    };
    script.onload = function() {
      if (library !== script || rendered()) return;
      if (typeof window.sc_flag !== 'function') {
        failed();
        return;
      }
      window.sc_flag(1739801, 'FFFFFF', '000000', 'cccccc', 2, 10, 0, 0);
      var requests = document.querySelectorAll('script[src*="service.supercounters.com/fc.php?id=1739801"]');
      var request = requests[requests.length - 1];
      if (request) request.onerror = function() {
        if (library === script) failed();
      };
    };
    // Keep the library tag in the widget: the vendor uses it as its insertion point.
    timeout = window.setTimeout(failed, 18000);
    widget.appendChild(script);
  }

  new MutationObserver(rendered).observe(widget, { childList: true, subtree: true });
  retry.addEventListener('click', function() {
    libraryRetries = 0;
    load();
  });
  load();
})();
