/* AjouCU Event Shared UI v20260814 - non-destructive progressive enhancement */
(function(){
  'use strict';
  function ready(fn){ if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',fn); else fn(); }
  ready(function(){
    document.body.classList.add('ajou-event-ui');

    // Keep legacy pages usable on mobile by making large tables horizontally scrollable.
    document.querySelectorAll('table').forEach(function(table){
      if(table.closest('.table-responsive,.ajou-mobile-table-wrap')) return;
      var parent=table.parentElement;
      if(!parent) return;
      var wrap=document.createElement('div');
      wrap.className='ajou-mobile-table-wrap';
      parent.insertBefore(wrap,table);
      wrap.appendChild(table);
    });

    // Improve tap ergonomics for legacy button-like inputs without changing their behavior.
    document.querySelectorAll('input[type="submit"],input[type="button"],button').forEach(function(el){
      if(!el.classList.contains('btn') && !el.classList.contains('close')) el.classList.add('ajou-legacy-action');
    });

    // Normalize numeric phone fields for mobile keyboards when the page used plain text inputs.
    document.querySelectorAll('input').forEach(function(input){
      var hint=((input.id||'')+' '+(input.name||'')+' '+(input.placeholder||'')).toLowerCase();
      if(input.type==='text' && /(phone|tel|mobile|contact|연락처|전화)/.test(hint)) input.setAttribute('inputmode','tel');
    });

    // External/new-window links get safer rel automatically.
    document.querySelectorAll('a[target="_blank"]').forEach(function(a){
      var rel=(a.getAttribute('rel')||'').split(/\s+/).filter(Boolean);
      ['noopener','noreferrer'].forEach(function(v){if(rel.indexOf(v)<0) rel.push(v);});
      a.setAttribute('rel',rel.join(' '));
    });
  });
})();
