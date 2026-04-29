// Vercel Web Analytics Integration
// This script initializes Vercel Web Analytics for the GuideFY application
// Based on: https://vercel.com/docs/analytics/quickstart

(function() {
  'use strict';
  
  // Initialize the analytics queue
  if (!window.va) {
    window.va = function() {
      (window.vaq = window.vaq || []).push(arguments);
    };
  }
  
  // Determine the environment
  var isDevelopment = false;
  try {
    // Check if we're in development (localhost or vercel preview)
    isDevelopment = window.location.hostname === 'localhost' || 
                   window.location.hostname === '127.0.0.1' ||
                   window.location.hostname.includes('vercel.app');
  } catch (e) {
    // Default to production
  }
  
  // Set the script source based on environment
  var scriptSrc = isDevelopment 
    ? 'https://va.vercel-scripts.com/v1/script.debug.js'
    : '/_vercel/insights/script.js';
  
  // Check if script is already loaded
  if (document.head.querySelector('script[src*="' + scriptSrc + '"]')) {
    return;
  }
  
  // Create and inject the analytics script
  var script = document.createElement('script');
  script.src = scriptSrc;
  script.defer = true;
  
  // Add SDK metadata
  script.setAttribute('data-sdkn', '@vercel/analytics');
  script.setAttribute('data-sdkv', '2.0.1');
  
  // Handle script load errors
  script.onerror = function() {
    var errorMessage = isDevelopment
      ? 'Please check if any ad blockers are enabled and try again.'
      : 'Be sure to enable Web Analytics for your project and deploy again. See https://vercel.com/docs/analytics/quickstart for more information.';
    console.log('[Vercel Web Analytics] Failed to load script from ' + scriptSrc + '. ' + errorMessage);
  };
  
  // Append script to head
  document.head.appendChild(script);
  
  if (isDevelopment) {
    console.log('[Vercel Web Analytics] Analytics initialized in development mode');
  }
})();
