/* ==========================================================================
   AppCopilot — Core Application JavaScript
   Mobile toggle, flash messages, smooth scroll, CSRF, utilities
   ========================================================================== */

(function () {
  'use strict';

  // -----------------------------------------------------------------------
  //  Wait for DOM
  // -----------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function () {
    initMobileNavbar();
    initFlashMessages();
    initSmoothScroll();
    initPageLoader();
    initRippleButtons();
  });

  // -----------------------------------------------------------------------
  //  1. Mobile Navbar Toggle
  // -----------------------------------------------------------------------
  function initMobileNavbar() {
    const toggleBtn = document.querySelector('.navbar-toggle');
    const navLinks = document.querySelector('.navbar-links');

    if (!toggleBtn || !navLinks) return;

    toggleBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      this.classList.toggle('active');
      navLinks.classList.toggle('open');
      document.body.classList.toggle('nav-open');
    });

    // Close on outside click
    document.addEventListener('click', function (e) {
      if (
        navLinks.classList.contains('open') &&
        !toggleBtn.contains(e.target) &&
        !navLinks.contains(e.target)
      ) {
        toggleBtn.classList.remove('active');
        navLinks.classList.remove('open');
        document.body.classList.remove('nav-open');
      }
    });

    // Close on link click (mobile)
    navLinks.querySelectorAll('a, button').forEach(function (link) {
      link.addEventListener('click', function () {
        if (window.innerWidth <= 768) {
          toggleBtn.classList.remove('active');
          navLinks.classList.remove('open');
          document.body.classList.remove('nav-open');
        }
      });
    });
  }

  // -----------------------------------------------------------------------
  //  2. Flash Message Auto-Dismiss
  // -----------------------------------------------------------------------
  function initFlashMessages() {
    var messages = document.querySelectorAll('.flash-message');
    var dismissTimers = new WeakMap();

    messages.forEach(function (msg) {
      var closeBtn = msg.querySelector('.flash-close');

      if (closeBtn) {
        closeBtn.addEventListener('click', function (e) {
          e.preventDefault();
          dismissFlash(msg);
        });
      }

      // Auto-dismiss after 5s (unless user hovers)
      var timer = setTimeout(function () {
        if (!msg.matches(':hover')) {
          dismissFlash(msg);
        } else {
          // Re-check when mouse leaves
          msg.addEventListener(
            'mouseleave',
            function () {
              dismissFlash(msg);
            },
            { once: true }
          );
        }
      }, 5000);

      dismissTimers.set(msg, timer);

      // Pause timer on hover
      msg.addEventListener('mouseenter', function () {
        var t = dismissTimers.get(msg);
        if (t) {
          clearTimeout(t);
          dismissTimers.set(msg, null);
        }
      });

      msg.addEventListener('mouseleave', function () {
        // Re-start timer if not already dismissing
        if (!msg.classList.contains('flash-dismissing')) {
          var newTimer = setTimeout(function () {
            dismissFlash(msg);
          }, 2000);
          dismissTimers.set(msg, newTimer);
        }
      });
    });

    function dismissFlash(msg) {
      if (msg.classList.contains('flash-dismissing')) return;
      msg.classList.add('flash-dismissing');
      var timer = dismissTimers.get(msg);
      if (timer) {
        clearTimeout(timer);
        dismissTimers.set(msg, null);
      }
      // Remove from DOM after animation
      msg.addEventListener(
        'animationend',
        function () {
          if (msg.parentNode) {
            msg.parentNode.removeChild(msg);
          }
        },
        { once: true }
      );
    }
  }

  // -----------------------------------------------------------------------
  //  3. Smooth Scroll for Anchor Links
  // -----------------------------------------------------------------------
  function initSmoothScroll() {
    document.addEventListener('click', function (e) {
      var link = e.target.closest('a[href^="#"]');
      if (!link) return;

      var targetId = link.getAttribute('href');
      if (targetId === '#' || targetId === '') return;

      var target = document.querySelector(targetId);
      if (!target) return;

      e.preventDefault();

      // Offset for fixed navbar
      var offset = 80; // navbar height + some padding
      var targetPosition =
        target.getBoundingClientRect().top + window.pageYOffset - offset;

      window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
      });

      // Focus the target for accessibility
      target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
    });
  }

  // -----------------------------------------------------------------------
  //  4. Page Loader Indicator
  // -----------------------------------------------------------------------
  function initPageLoader() {
    var loader = document.querySelector('.page-loader');

    if (!loader) return;

    // Hide loader once page is fully loaded
    if (document.readyState === 'complete') {
      hideLoader(loader);
    } else {
      window.addEventListener('load', function () {
        hideLoader(loader);
      });
    }

    // Also hide on error after a timeout (prevents stuck loader)
    setTimeout(function () {
      if (loader && !loader.classList.contains('hidden')) {
        hideLoader(loader);
      }
    }, 10000);

    function hideLoader(el) {
      el.classList.add('hidden');
      // Remove from DOM after transition
      setTimeout(function () {
        if (el.parentNode) {
          el.parentNode.removeChild(el);
        }
      }, 500);
    }
  }

  // -----------------------------------------------------------------------
  //  5. Ripple Effect on Buttons
  // -----------------------------------------------------------------------
  function initRippleButtons() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.btn');
      if (!btn) return;

      var rect = btn.getBoundingClientRect();
      var size = Math.max(rect.width, rect.height);
      var x = e.clientX - rect.left - size / 2;
      var y = e.clientY - rect.top - size / 2;

      var ripple = document.createElement('span');
      ripple.className = 'ripple';
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';

      btn.appendChild(ripple);

      ripple.addEventListener('animationend', function () {
        ripple.parentNode.removeChild(ripple);
      });
    });
  }

  // =======================================================================
  //  EXPORTED UTILITIES (attached to window for use by other scripts)
  // =======================================================================

  /**
   * Read CSRF token from meta tag.
   * @param {boolean} [returnHeader=false] - If true, returns { header, value } object.
   * @returns {string|{header:string, value:string}}
   */
  window.getCSRFToken = function (returnHeader) {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (!meta) {
      console.warn('[AppCopilot] CSRF meta tag not found');
      return returnHeader ? { header: 'X-CSRFToken', value: '' } : '';
    }
    var token = meta.getAttribute('content');
    return returnHeader ? { header: 'X-CSRFToken', value: token } : token;
  };

  /**
   * Format a date string or Date object to Brazilian locale (pt-BR)
   * with time. Falls back gracefully.
   * @param {string|Date} dateInput
   * @param {object} [options] - Intl.DateTimeFormat options
   * @returns {string}
   */
  window.formatDate = function (dateInput, options) {
    try {
      var date =
        typeof dateInput === 'string' ? new Date(dateInput) : dateInput;

      if (!(date instanceof Date) || isNaN(date.getTime())) {
        return String(dateInput || '');
      }

      var defaultOptions = {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      };

      var mergedOptions = Object.assign({}, defaultOptions, options || {});

      // Use pt-BR for default locale
      return date.toLocaleDateString('pt-BR', mergedOptions);
    } catch (e) {
      console.warn('[AppCopilot] formatDate error:', e);
      return String(dateInput || '');
    }
  };

  /**
   * Programmatically show a flash message.
   * @param {string} message - The message text.
   * @param {string} [type='info'] - One of: success, error, warning, info.
   * @param {number} [duration=5000] - Auto-dismiss duration in ms.
   */
  window.showFlash = function (message, type, duration) {
    if (!message) return;

    type = type || 'info';
    duration = duration || 5000;

    var container = document.querySelector('.flash-container');
    if (!container) {
      // Auto-create container if it doesn't exist
      container = document.createElement('div');
      container.className = 'flash-container';
      document.body.appendChild(container);
    }

    // Icon mapping
    var icons = {
      success:
        '<svg class="flash-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>',
      error:
        '<svg class="flash-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>',
      warning:
        '<svg class="flash-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>',
      info:
        '<svg class="flash-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>'
    };

    var el = document.createElement('div');
    el.className = 'flash-message flash-' + type;
    el.innerHTML =
      '<div class="flash-icon-wrap">' +
      (icons[type] || icons.info) +
      '</div>' +
      '<div class="flash-body">' +
      escapeHtml(message) +
      '</div>' +
      '<button class="flash-close" aria-label="Fechar">&times;</button>';

    container.appendChild(el);

    // Wire close
    var closeBtn = el.querySelector('.flash-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        dismissProgrammaticFlash(el);
      });
    }

    // Auto-dismiss
    var timer = setTimeout(function () {
      dismissProgrammaticFlash(el);
    }, duration);

    // Pause on hover
    el.addEventListener('mouseenter', function () {
      clearTimeout(timer);
    });

    el.addEventListener('mouseleave', function () {
      timer = setTimeout(function () {
        dismissProgrammaticFlash(el);
      }, 2000);
    });

    function dismissProgrammaticFlash(msgEl) {
      if (msgEl.classList.contains('flash-dismissing')) return;
      msgEl.classList.add('flash-dismissing');
      clearTimeout(timer);
      msgEl.addEventListener(
        'animationend',
        function () {
          if (msgEl.parentNode) {
            msgEl.parentNode.removeChild(msgEl);
          }
        },
        { once: true }
      );
    }
  };

  // -----------------------------------------------------------------------
  //  Helper: escape HTML to prevent XSS in injected flash messages
  // -----------------------------------------------------------------------
  function escapeHtml(text) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
  }

  // -----------------------------------------------------------------------
  //  Initialize any existing flash messages (for pages with pre-rendered)
  // -----------------------------------------------------------------------
  // Re-run flash init for dynamically added messages
  var flashObserver = new MutationObserver(function () {
    var uninitialized = document.querySelectorAll(
      '.flash-message:not([data-flash-init])'
    );
    uninitialized.forEach(function (msg) {
      msg.setAttribute('data-flash-init', '1');
      var closeBtn = msg.querySelector('.flash-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', function (e) {
          e.preventDefault();
          msg.classList.add('flash-dismissing');
          msg.addEventListener(
            'animationend',
            function () {
              if (msg.parentNode) msg.parentNode.removeChild(msg);
            },
            { once: true }
          );
        });
      }
      var timer = setTimeout(function () {
        if (!msg.matches(':hover')) {
          msg.classList.add('flash-dismissing');
          msg.addEventListener(
            'animationend',
            function () {
              if (msg.parentNode) msg.parentNode.removeChild(msg);
            },
            { once: true }
          );
        }
      }, 5000);
      msg.addEventListener('mouseenter', function () {
        clearTimeout(timer);
      });
      msg.addEventListener('mouseleave', function () {
        timer = setTimeout(function () {
          msg.classList.add('flash-dismissing');
          msg.addEventListener(
            'animationend',
            function () {
              if (msg.parentNode) msg.parentNode.removeChild(msg);
            },
            { once: true }
          );
        }, 2000);
      });
    });
  });

  if (document.body) {
    flashObserver.observe(document.body, { childList: true, subtree: true });
  }

  // -----------------------------------------------------------------------
  //  Expose version for debugging
  // -----------------------------------------------------------------------
  window.__APPCOPILOT = window.__APPCOPILOT || {};
  window.__APPCOPILOT.version = '1.0.0';
  window.__APPCOPILOT.app = 'AppCopilot';

})();
