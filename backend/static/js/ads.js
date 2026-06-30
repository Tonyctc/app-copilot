/* ==========================================================================
   AppCopilot — Ad Management JavaScript
   Injects ad placeholders, tracks impressions in localStorage, revenue sim
   ========================================================================== */

(function () {
  'use strict';

  // -----------------------------------------------------------------------
  //  Configuration
  // -----------------------------------------------------------------------
  var CONFIG = {
    // Whether ads are enabled (read from body data attribute)
    adsEnabledAttr: 'data-ads-enabled',

    // Storage keys
    storageKey: 'appcopilot_ad_impressions',
    storageRevenueKey: 'appcopilot_ad_revenue',

    // Simulated revenue per impression (in cents)
    revenuePerImpression: 0.05,

    // Impression tracking dedup window (ms)
    dedupWindow: 30000,

    // Default ad sizes
    sizes: {
      rectangle: { width: 300, height: 250, label: 'Retângulo' },
      banner: { width: 728, height: 90, label: 'Banner' },
      skyscraper: { width: 160, height: 600, label: 'Skyscraper' },
      leaderboard: { width: 728, height: 90, label: 'Leaderboard' }
    }
  };

  // -----------------------------------------------------------------------
  //  State
  // -----------------------------------------------------------------------
  var adsEnabled = false;
  var impressionTimestamps = [];

  // -----------------------------------------------------------------------
  //  DOM Ready
  // -----------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function () {
    initAds();
  });

  // -----------------------------------------------------------------------
  //  Initialization
  // -----------------------------------------------------------------------
  function initAds() {
    var body = document.body;

    // Check if ads are enabled via data attribute on <body>
    adsEnabled =
      body.getAttribute(CONFIG.adsEnabledAttr) === 'true' ||
      body.getAttribute(CONFIG.adsEnabledAttr) === '1';

    if (!adsEnabled) {
      // Optionally hide ad containers
      var containers = document.querySelectorAll('.ad-container');
      containers.forEach(function (c) {
        c.style.display = 'none';
      });
      return;
    }

    // Load impression history from localStorage
    loadImpressionHistory();

    // Inject ads into all ad containers on the page
    var adContainers = document.querySelectorAll('.ad-container');
    adContainers.forEach(function (container) {
      injectAd(container);
    });

    // Expose refresh function so other parts of the app can re-init ads
    window.__APPCOPILOT_ADS = {
      refresh: function () {
        document.querySelectorAll('.ad-container').forEach(function (c) {
          // Only inject if empty
          if (!c.querySelector('.ad-inner')) {
            injectAd(c);
          }
        });
      },
      getStats: getAdStats,
      isEnabled: function () {
        return adsEnabled;
      }
    };
  }

  // -----------------------------------------------------------------------
  //  Inject Ad into a single container
  // -----------------------------------------------------------------------
  function injectAd(container) {
    // Determine ad size variant from class
    var variant = getAdVariant(container);
    var sizeInfo = CONFIG.sizes[variant] || CONFIG.sizes.banner;

    // Build ad HTML
    var adInner = document.createElement('div');
    adInner.className = 'ad-inner';
    adInner.style.cssText =
      'display:flex;flex-direction:column;align-items:center;justify-content:center;' +
      'width:100%;min-height:' +
      sizeInfo.height +
      'px;' +
      'text-align:center;padding:16px;';

    // Label
    var label = document.createElement('span');
    label.className = 'ad-label';
    label.textContent = '— Anúncio —';
    label.style.cssText =
      'font-size:10px;text-transform:uppercase;letter-spacing:2px;' +
      'color:#64748b;margin-bottom:8px;';

    // Placeholder content (simulating Google AdSense style)
    var placeholder = document.createElement('div');
    placeholder.className = 'ad-placeholder';
    placeholder.style.cssText =
      'display:flex;flex-direction:column;align-items:center;gap:6px;' +
      'color:#94a3b8;font-size:13px;';

    // Ad icon (simulated)
    var icon = document.createElement('span');
    icon.textContent = '📢';
    icon.style.cssText = 'font-size:24px;opacity:0.5;';

    var text = document.createElement('span');
    text.textContent =
      'Conteúdo Patrocinado · ' +
      sizeInfo.width +
      'x' +
      sizeInfo.height;

    placeholder.appendChild(icon);
    placeholder.appendChild(text);

    adInner.appendChild(label);
    adInner.appendChild(placeholder);

    // Clear container and append
    container.innerHTML = '';
    container.appendChild(adInner);

    // Track impression (with dedup)
    trackImpression(container, variant);
  }

  // -----------------------------------------------------------------------
  //  Determine ad variant from container class
  // -----------------------------------------------------------------------
  function getAdVariant(container) {
    var classList = container.className.split(/\s+/);
    var knownVariants = Object.keys(CONFIG.sizes);

    for (var i = 0; i < classList.length; i++) {
      var cls = classList[i];
      // Check for classes like "ad-rectangle", "ad-banner", etc.
      var match = cls.match(/^ad-(\w+)$/);
      if (match && knownVariants.indexOf(match[1]) !== -1) {
        return match[1];
      }
    }

    // Default: check data attribute
    var dataSize = container.getAttribute('data-ad-size');
    if (dataSize && knownVariants.indexOf(dataSize) !== -1) {
      return dataSize;
    }

    return 'banner';
  }

  // -----------------------------------------------------------------------
  //  Impression Tracking (localStorage)
  // -----------------------------------------------------------------------
  function trackImpression(container, variant) {
    var now = Date.now();
    var containerKey = getContainerKey(container);

    // Dedup: skip if same container was tracked within dedup window
    var recent = impressionTimestamps.filter(function (entry) {
      return (
        entry.key === containerKey &&
        now - entry.timestamp < CONFIG.dedupWindow
      );
    });

    if (recent.length > 0) {
      return; // Skip duplicate impression
    }

    // Record impression
    var impression = {
      key: containerKey,
      variant: variant,
      timestamp: now,
      date: new Date().toISOString()
    };

    impressionTimestamps.push(impression);

    // Update revenue
    var revenue = getStoredRevenue() + CONFIG.revenuePerImpression;

    // Persist to localStorage
    try {
      localStorage.setItem(
        CONFIG.storageKey,
        JSON.stringify(impressionTimestamps)
      );
      localStorage.setItem(
        CONFIG.storageRevenueKey,
        revenue.toFixed(4)
      );
    } catch (e) {
      // localStorage may be full or unavailable — silently degrade
      console.warn('[Ads] localStorage unavailable:', e.message);
    }
  }

  // -----------------------------------------------------------------------
  //  Generate unique key for a container (based on position in DOM)
  // -----------------------------------------------------------------------
  function getContainerKey(container) {
    // Use a combination of parent path and index for uniqueness
    var parent = container.parentNode;
    var index = 0;
    if (parent) {
      var siblings = parent.querySelectorAll('.ad-container');
      siblings.forEach(function (sib, i) {
        if (sib === container) {
          index = i;
        }
      });
    }
    return 'ad_' + index + '_' + (container.className || '');
  }

  // -----------------------------------------------------------------------
  //  Load impression history from storage
  // -----------------------------------------------------------------------
  function loadImpressionHistory() {
    try {
      var stored = localStorage.getItem(CONFIG.storageKey);
      if (stored) {
        impressionTimestamps = JSON.parse(stored);
        // Ensure it's an array
        if (!Array.isArray(impressionTimestamps)) {
          impressionTimestamps = [];
        }
      }

      // Cleanup old entries (older than 30 days)
      var thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
      impressionTimestamps = impressionTimestamps.filter(function (entry) {
        return entry.timestamp > thirtyDaysAgo;
      });
    } catch (e) {
      impressionTimestamps = [];
    }
  }

  // -----------------------------------------------------------------------
  //  Get stored revenue
  // -----------------------------------------------------------------------
  function getStoredRevenue() {
    try {
      var stored = localStorage.getItem(CONFIG.storageRevenueKey);
      return stored ? parseFloat(stored) : 0;
    } catch (e) {
      return 0;
    }
  }

  // -----------------------------------------------------------------------
  //  Get ad statistics (for admin dashboard)
  // -----------------------------------------------------------------------
  function getAdStats() {
    var now = Date.now();
    var oneDay = 24 * 60 * 60 * 1000;

    // Total impressions
    var totalImpressions = impressionTimestamps.length;

    // Today's impressions
    var todayStart = new Date();
    todayStart.setHours(0, 0, 0, 0);
    var todayImpressions = impressionTimestamps.filter(function (entry) {
      return entry.timestamp >= todayStart.getTime();
    }).length;

    // This week's impressions
    var weekStart = now - 7 * oneDay;
    var weekImpressions = impressionTimestamps.filter(function (entry) {
      return entry.timestamp >= weekStart;
    }).length;

    // This month's impressions
    var monthStart = now - 30 * oneDay;
    var monthImpressions = impressionTimestamps.filter(function (entry) {
      return entry.timestamp >= monthStart;
    }).length;

    // Revenue
    var totalRevenue = getStoredRevenue();

    // Impressions by variant
    var byVariant = {};
    impressionTimestamps.forEach(function (entry) {
      var v = entry.variant || 'unknown';
      byVariant[v] = (byVariant[v] || 0) + 1;
    });

    return {
      enabled: adsEnabled,
      totalImpressions: totalImpressions,
      todayImpressions: todayImpressions,
      weekImpressions: weekImpressions,
      monthImpressions: monthImpressions,
      totalRevenue: totalRevenue,
      revenueFormatted: 'R$ ' + (totalRevenue / 100).toFixed(2),
      byVariant: byVariant,
      impressions: impressionTimestamps.slice(-100) // last 100 for detail
    };
  }

  // -----------------------------------------------------------------------
  //  Expose public API
  // -----------------------------------------------------------------------
  window.__APPCOPILOT_ADS = window.__APPCOPILOT_ADS || {
    refresh: function () {
      document.querySelectorAll('.ad-container').forEach(function (c) {
        if (!c.querySelector('.ad-inner')) {
          injectAd(c);
        }
      });
    },
    getStats: getAdStats,
    isEnabled: function () {
      return adsEnabled;
    }
  };

  // -----------------------------------------------------------------------
  //  Handle dynamic content loading — observe for new ad containers
  // -----------------------------------------------------------------------
  if (typeof MutationObserver !== 'undefined') {
    var adObserver = new MutationObserver(function (mutations) {
      if (!adsEnabled) return;

      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === 1) {
            // Element node
            if (node.classList && node.classList.contains('ad-container')) {
              injectAd(node);
            }
            // Check for containers inside the added subtree
            var innerContainers = node.querySelectorAll
              ? node.querySelectorAll('.ad-container')
              : [];
            innerContainers.forEach(function (c) {
              if (!c.querySelector('.ad-inner')) {
                injectAd(c);
              }
            });
          }
        });
      });
    });

    if (document.body) {
      adObserver.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  }

  // -----------------------------------------------------------------------
  //  Cleanup old data on page unload (optional, for data hygiene)
  // -----------------------------------------------------------------------
  window.addEventListener('beforeunload', function () {
    // Trim impression history to last 30 days on unload
    try {
      var thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000;
      var trimmed = impressionTimestamps.filter(function (entry) {
        return entry.timestamp > thirtyDaysAgo;
      });
      localStorage.setItem(
        CONFIG.storageKey,
        JSON.stringify(trimmed)
      );
    } catch (e) {
      // Silently fail
    }
  });

  console.log('[Ads] AppCopilot ad module initialized. Enabled:', adsEnabled);

})();
