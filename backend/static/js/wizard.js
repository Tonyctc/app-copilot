/* ==========================================================================
   AppCopilot — Wizard JavaScript
   Form validation, AJAX submission, phase navigation, progress, checklist
   ========================================================================== */

(function () {
  'use strict';

  // -----------------------------------------------------------------------
  //  State
  // -----------------------------------------------------------------------
  var state = {
    currentPhase: 1,
    totalPhases: 4,
    submittedData: {},
    isSubmitting: false,
    answersVisible: false
  };

  var selectors = {
    phasePanels: '.phase-panel',
    phaseSteps: '.phase-step',
    phaseStepper: '.phase-stepper',
    progressFill: '.progress-fill',
    progressPct: '.progress-pct',
    progressLabel: '.progress-label',
    prevAnswers: '.previous-answers',
    prevAnswersToggle: '.toggle-answers',
    deliveryChecklist: '.delivery-checklist',
    wizardForm: '.phase-form',
    nextBtn: '.btn-next',
    prevBtn: '.btn-prev',
    saveBtn: '.btn-save',
    submitBtn: '.btn-submit'
  };

  // -----------------------------------------------------------------------
  //  DOM Ready
  // -----------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function () {
    if (!document.querySelector(selectors.phasePanels)) return; // not a wizard page

    cacheElements();
    bindEvents();
    showPhase(state.currentPhase);
    updateProgress();
    initDeliveryChecklist();
  });

  // -----------------------------------------------------------------------
  //  Cached DOM refs
  // -----------------------------------------------------------------------
  var $ = {};
  var _cached = false;

  function cacheElements() {
    if (_cached) return;
    $.panels = document.querySelectorAll(selectors.phasePanels);
    $.steps = document.querySelectorAll(selectors.phaseSteps);
    $.stepper = document.querySelector(selectors.phaseStepper);
    $.progressFill = document.querySelector(selectors.progressFill);
    $.progressPct = document.querySelector(selectors.progressPct);
    $.progressLabel = document.querySelector(selectors.progressLabel);
    $.prevAnswers = document.querySelector(selectors.prevAnswers);
    $.prevAnswersToggle = document.querySelector(selectors.prevAnswersToggle);
    $.checklist = document.querySelector(selectors.deliveryChecklist);
    $.form = document.querySelector(selectors.wizardForm);
    _cached = true;
  }

  // -----------------------------------------------------------------------
  //  Event Binding
  // -----------------------------------------------------------------------
  function bindEvents() {
    // Next buttons
    document.querySelectorAll(selectors.nextBtn).forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        goToNextPhase();
      });
    });

    // Previous buttons
    document.querySelectorAll(selectors.prevBtn).forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        goToPrevPhase();
      });
    });

    // Save buttons (AJAX) — DISABLED: handled by inline JS per-form
    // document.querySelectorAll(selectors.saveBtn).forEach(function (btn) {
    //   btn.addEventListener('click', function (e) {
    //     e.preventDefault();
    //     submitCurrentPhase('save');
    //   });
    // });

    // Submit buttons (final) — DISABLED: handled by inline JS per-form
    // document.querySelectorAll(selectors.submitBtn).forEach(function (btn) {
    //   btn.addEventListener('click', function (e) {
    //     e.preventDefault();
    //     submitCurrentPhase('submit');
    //   });
    // });

    // Phase step clicks (stepper navigation)
    $.steps.forEach(function (step) {
      step.addEventListener('click', function () {
        var phase = parseInt(this.getAttribute('data-phase'), 10);
        if (!isNaN(phase)) {
          navigateToPhase(phase);
        }
      });
    });

    // Toggle previous answers
    if ($.prevAnswersToggle) {
      $.prevAnswersToggle.addEventListener('click', function (e) {
        e.preventDefault();
        togglePreviousAnswers();
      });
    }

    // Auto-save on form changes (debounced)
    if ($.form) {
      var autoSaveTimer = null;
      $.form.addEventListener('change', function () {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(function () {
          if (state.currentPhase > 1) {
            autoSaveCurrentPhase();
          }
        }, 3000);
      });
    }

    // Keyboard navigation
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        var activeInput = document.activeElement;
        if (
          activeInput &&
          activeInput.closest(selectors.phasePanels + '.active') &&
          !activeInput.closest('textarea') &&
          !activeInput.closest('button')
        ) {
          // Don't submit on Enter in textareas or buttons
          e.preventDefault();
          goToNextPhase();
        }
      }
    });

    // Handle form submission via Enter key on selects/inputs
    $.panels.forEach(function (panel) {
      panel.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          var target = e.target;
          if (
            target.tagName === 'INPUT' &&
            target.type !== 'textarea' &&
            !target.closest('button')
          ) {
            e.preventDefault();
            goToNextPhase();
          }
        }
      });
    });
  }

  // -----------------------------------------------------------------------
  //  Phase Navigation
  // -----------------------------------------------------------------------
  function showPhase(phaseNum) {
    var valid = validateCurrentPhase(false);

    // Show/hide panels
    $.panels.forEach(function (panel) {
      var p = parseInt(panel.getAttribute('data-phase'), 10);
      panel.classList.toggle('active', p === phaseNum);
    });

    // Update stepper
    $.steps.forEach(function (step) {
      var p = parseInt(step.getAttribute('data-phase'), 10);
      step.classList.remove('active', 'completed', 'upcoming');
      if (p < phaseNum) {
        step.classList.add('completed');
      } else if (p === phaseNum) {
        step.classList.add('active');
      } else {
        step.classList.add('upcoming');
      }
    });

    // Update progress bar
    updateProgress();

    // Auto-scroll to active phase panel
    var activePanel = document.querySelector(
      selectors.phasePanels + '.active'
    );
    if (activePanel) {
      var offset = 100;
      var targetPosition =
        activePanel.getBoundingClientRect().top +
        window.pageYOffset -
        offset;
      window.scrollTo({ top: targetPosition, behavior: 'smooth' });
    }

    // Update prev answers visibility
    if (state.currentPhase !== phaseNum) {
      state.answersVisible = false;
      if ($.prevAnswers) {
        $.prevAnswers.classList.remove('open');
      }
    }

    state.currentPhase = phaseNum;
  }

  function goToNextPhase() {
    if (state.currentPhase >= state.totalPhases) return;

    if (!validateCurrentPhase(true)) {
      // Flash error about required fields
      if (window.showFlash) {
        window.showFlash(
          'Preencha todos os campos obrigatórios antes de continuar.',
          'error'
        );
      }
      return;
    }

    // Collect data from current phase
    collectCurrentPhaseData();

    // Save before moving
    autoSaveCurrentPhase();

    showPhase(state.currentPhase + 1);
  }

  function goToPrevPhase() {
    if (state.currentPhase <= 1) return;

    collectCurrentPhaseData();
    showPhase(state.currentPhase - 1);
  }

  function navigateToPhase(phase) {
    if (phase === state.currentPhase) return;

    // Can navigate back freely, but moving forward requires validation
    if (phase > state.currentPhase) {
      // Validate all phases between current and target
      for (var i = state.currentPhase; i < phase; i++) {
        // Temporarily show the phase to validate it
        var origPhase = state.currentPhase;
        showPhase(i);
        if (!validateCurrentPhase(true)) {
          showPhase(origPhase);
          if (window.showFlash) {
            window.showFlash(
              'Complete a fase ' +
                i +
                ' antes de prosseguir.',
              'error'
            );
          }
          return;
        }
        collectCurrentPhaseData();
      }
    }

    showPhase(phase);
    updateProgress();
  }

  // -----------------------------------------------------------------------
  //  Form Validation
  // -----------------------------------------------------------------------
  function validateCurrentPhase(showErrors) {
    var activePanel = document.querySelector(
      selectors.phasePanels + '.active'
    );
    if (!activePanel) return true;

    var requiredFields = activePanel.querySelectorAll('[required]');
    var allValid = true;

    requiredFields.forEach(function (field) {
      var value = field.value ? field.value.trim() : '';
      var isValid = false;

      if (field.tagName === 'SELECT') {
        isValid = value !== '' && value !== 'selecione' && value !== 'none';
      } else if (field.type === 'checkbox') {
        if (field.closest('.delivery-checklist')) {
          // Checklist items are validated separately
          isValid = true;
        } else {
          isValid = field.checked;
        }
      } else if (field.type === 'radio') {
        var name = field.name;
        var checked = activePanel.querySelector(
          'input[name="' + name + '"]:checked'
        );
        isValid = checked !== null;
      } else {
        isValid = value.length > 0;
      }

      if (!isValid) {
        allValid = false;
        if (showErrors) {
          field.classList.add('error');
          // Add error message if not exists
          var errorEl = field.parentNode.querySelector('.form-error');
          if (!errorEl) {
            errorEl = document.createElement('span');
            errorEl.className = 'form-error';
            errorEl.textContent = 'Campo obrigatório';
            field.parentNode.appendChild(errorEl);
          }
        }
      } else {
        field.classList.remove('error');
        var existingError = field.parentNode.querySelector('.form-error');
        if (existingError) {
          existingError.remove();
        }
      }
    });

    // Validate delivery checklist if present
    var checklist = activePanel.querySelector(selectors.deliveryChecklist);
    if (checklist) {
      var checklistItems = checklist.querySelectorAll('.checklist-item');
      var checkedItems = checklist.querySelectorAll(
        '.checklist-item.checked'
      );
      if (checklistItems.length > 0 && checkedItems.length === 0) {
        allValid = false;
        if (showErrors) {
          if (window.showFlash) {
            window.showFlash(
              'Marque pelo menos um item da checklist de entrega.',
              'warning'
            );
          }
        }
      }
    }

    return allValid;
  }

  // -----------------------------------------------------------------------
  //  Collect data from current phase
  // -----------------------------------------------------------------------
  function collectCurrentPhaseData() {
    var activePanel = document.querySelector(
      selectors.phasePanels + '.active'
    );
    if (!activePanel) return;

    var fields = activePanel.querySelectorAll(
      'input, textarea, select'
    );
    var phaseData = {};
    var phaseNum = parseInt(activePanel.getAttribute('data-phase'), 10);

    fields.forEach(function (field) {
      if (
        field.type === 'submit' ||
        field.type === 'button' ||
        !field.name
      ) {
        return;
      }

      var name = field.name;
      var value;

      if (field.type === 'checkbox') {
        if (field.closest('.delivery-checklist')) {
          // Checklist items tracked by data-key
          var key = field.getAttribute('data-key') || name;
          phaseData[key] = field.checked ? 'true' : 'false';
        } else {
          if (!phaseData[name]) phaseData[name] = [];
          if (field.checked) phaseData[name].push(field.value);
        }
        return;
      } else if (field.type === 'radio') {
        if (field.checked) {
          phaseData[name] = field.value;
        }
        return;
      } else {
        value = field.value ? field.value.trim() : '';
      }

      phaseData[name] = value;
    });

    state.submittedData['phase_' + phaseNum] = phaseData;
  }

  // -----------------------------------------------------------------------
  //  AJAX Form Submission
  // -----------------------------------------------------------------------
  function submitCurrentPhase(action) {
    if (state.isSubmitting) return;

    // Validate all phases before final submit
    if (action === 'submit') {
      for (var i = 1; i <= state.totalPhases; i++) {
        showPhase(i);
        if (!validateCurrentPhase(true)) {
          if (window.showFlash) {
            window.showFlash(
              'Corrija os erros na fase ' + i + ' antes de finalizar.',
              'error'
            );
          }
          return;
        }
        collectCurrentPhaseData();
      }
    } else {
      if (!validateCurrentPhase(true)) {
        if (window.showFlash) {
          window.showFlash(
            'Preencha todos os campos obrigatórios.',
            'error'
          );
        }
        return;
      }
      collectCurrentPhaseData();
    }

    state.isSubmitting = true;
    var saveBtn =
      document.querySelector(selectors.saveBtn) ||
      document.querySelector(selectors.submitBtn);
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerHTML =
        '<span class="spinner spinner-sm spinner-white"></span> Salvando...';
    }

    var csrfToken = window.getCSRFToken(true);
    var url =
      action === 'submit'
        ? ($.form ? $.form.getAttribute('data-submit-url') : null) ||
          '/wizard/submit'
        : ($.form ? $.form.getAttribute('data-save-url') : null) ||
          '/wizard/save';

    // Gather all data
    var allData = {};
    for (var phaseKey in state.submittedData) {
      if (state.submittedData.hasOwnProperty(phaseKey)) {
        var phaseData = state.submittedData[phaseKey];
        for (var fieldName in phaseData) {
          if (phaseData.hasOwnProperty(fieldName)) {
            allData[fieldName] = phaseData[fieldName];
          }
        }
      }
    }
    allData.action = action;

    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    if (csrfToken.value) {
      xhr.setRequestHeader(csrfToken.header, csrfToken.value);
    }

    xhr.onload = function () {
      state.isSubmitting = false;
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.textContent =
          action === 'submit' ? 'Finalizar' : 'Salvar Rascunho';
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          var response = JSON.parse(xhr.responseText);

          if (response.success) {
            if (window.showFlash) {
              window.showFlash(
                response.message ||
                  (action === 'submit'
                    ? 'Especificação finalizada com sucesso!'
                    : 'Rascunho salvo com sucesso.'),
                'success'
              );
            }

            // On final submit, redirect if URL provided
            if (action === 'submit' && response.redirect_url) {
              setTimeout(function () {
                window.location.href = response.redirect_url;
              }, 1500);
            } else if (action === 'submit' && response.redirect) {
              setTimeout(function () {
                window.location.href = response.redirect;
              }, 1500);
            }
          } else {
            if (window.showFlash) {
              window.showFlash(
                response.message || 'Erro ao salvar. Tente novamente.',
                'error'
              );
            }
          }
        } catch (e) {
          if (window.showFlash) {
            window.showFlash('Resposta inválida do servidor.', 'error');
          }
        }
      } else if (xhr.status === 422) {
        try {
          var errResponse = JSON.parse(xhr.responseText);
          if (errResponse.errors) {
            highlightServerErrors(errResponse.errors);
          }
          if (window.showFlash) {
            window.showFlash(
              errResponse.message || 'Dados inválidos. Verifique os campos.',
              'error'
            );
          }
        } catch (e) {
          if (window.showFlash) {
            window.showFlash('Erro de validação no servidor.', 'error');
          }
        }
      } else if (xhr.status === 401) {
        if (window.showFlash) {
          window.showFlash('Sessão expirada. Faça login novamente.', 'error');
        }
        setTimeout(function () {
          window.location.href = '/login';
        }, 2000);
      } else {
        if (window.showFlash) {
          window.showFlash(
            'Erro do servidor (' + xhr.status + '). Tente novamente.',
            'error'
          );
        }
      }
    };

    xhr.onerror = function () {
      state.isSubmitting = false;
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.textContent =
          action === 'submit' ? 'Finalizar' : 'Salvar Rascunho';
      }
      if (window.showFlash) {
        window.showFlash(
          'Erro de conexão. Verifique sua internet.',
          'error'
        );
      }
    };

    xhr.send(JSON.stringify(allData));
  }

  // -----------------------------------------------------------------------
  //  Auto-save current phase (silent)
  // -----------------------------------------------------------------------
  function autoSaveCurrentPhase() {
    if (!validateCurrentPhase(false)) return;

    collectCurrentPhaseData();

    var csrfToken = window.getCSRFToken(true);
    var url =
      ($.form ? $.form.getAttribute('data-auto-save-url') : null) ||
      '/wizard/auto-save';

    var allData = {};
    for (var phaseKey in state.submittedData) {
      if (state.submittedData.hasOwnProperty(phaseKey)) {
        var phaseData = state.submittedData[phaseKey];
        for (var fieldName in phaseData) {
          if (phaseData.hasOwnProperty(fieldName)) {
            allData[fieldName] = phaseData[fieldName];
          }
        }
      }
    }

    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    if (csrfToken.value) {
      xhr.setRequestHeader(csrfToken.header, csrfToken.value);
    }

    // Silent — no UI feedback on success
    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        // Update last saved timestamp if element exists
        var savedEl = document.querySelector('.last-saved');
        if (savedEl) {
          var now = new Date();
          savedEl.textContent =
            'Salvo às ' +
            now.getHours().toString().padStart(2, '0') +
            ':' +
            now.getMinutes().toString().padStart(2, '0');
        }
      }
    };

    xhr.send(JSON.stringify(allData));
  }

  // -----------------------------------------------------------------------
  //  Highlight server-side validation errors
  // -----------------------------------------------------------------------
  function highlightServerErrors(errors) {
    if (!errors || typeof errors !== 'object') return;

    for (var fieldName in errors) {
      if (errors.hasOwnProperty(fieldName)) {
        var field = document.querySelector('[name="' + fieldName + '"]');
        if (field) {
          field.classList.add('error');
          var errorContainer = field.parentNode.querySelector('.form-error');
          if (!errorContainer) {
            errorContainer = document.createElement('span');
            errorContainer.className = 'form-error';
            field.parentNode.appendChild(errorContainer);
          }
          errorContainer.textContent =
            errors[fieldName] || 'Campo inválido';

          // Scroll to first error
          if (document.querySelector('.form-error')) {
            var firstError = document.querySelector('.form-error');
            firstError.scrollIntoView({
              behavior: 'smooth',
              block: 'center'
            });
          }
        }
      }
    }
  }

  // -----------------------------------------------------------------------
  //  Progress Percentage Calculation and Update
  // -----------------------------------------------------------------------
  function updateProgress() {
    var completedPhases = state.currentPhase - 1;
    if (state.currentPhase > 0) {
      // Count completed steps in stepper
      completedPhases = document.querySelectorAll(
        selectors.phaseSteps + '.completed'
      ).length;
    }

    var pct = Math.round((completedPhases / state.totalPhases) * 100);
    pct = Math.min(pct, 100);

    if ($.progressFill) {
      $.progressFill.style.width = pct + '%';
    }

    if ($.progressPct) {
      $.progressPct.textContent = pct + '%';
    }

    if ($.progressLabel) {
      var labels = [
        'Iniciando',
        'Descoberta',
        'Definição',
        'Desenvolvimento',
        'Entrega'
      ];
      var labelIndex = Math.min(completedPhases, labels.length - 1);
      $.progressLabel.textContent = labels[labelIndex] || '';
    }

    // Update stepper gradient line
    if ($.stepper) {
      $.stepper.style.setProperty('--progress-pct', pct + '%');
      $.stepper.classList.add('has-progress');
    }
  }

  // -----------------------------------------------------------------------
  //  Delivery Checklist Validation
  // -----------------------------------------------------------------------
  function initDeliveryChecklist() {
    if (!$.checklist) return;

    var items = $.checklist.querySelectorAll('.checklist-item');

    items.forEach(function (item) {
      // Each item has a checkbox or clickable area
      var checkbox = item.querySelector('input[type="checkbox"]');
      if (checkbox) {
        checkbox.addEventListener('change', function () {
          item.classList.toggle('checked', this.checked);
        });
      }

      // Also make the whole item clickable
      item.addEventListener('click', function (e) {
        // Don't toggle if clicking a link or button inside
        if (e.target.closest('a') || e.target.closest('button')) return;

        var cb = this.querySelector('input[type="checkbox"]');
        if (cb) {
          cb.checked = !cb.checked;
          this.classList.toggle('checked', cb.checked);

          // Trigger change event
          var evt = document.createEvent('HTMLEvents');
          evt.initEvent('change', true, false);
          cb.dispatchEvent(evt);
        }
      });
    });

    // Update progress indicator for checklist
    updateChecklistProgress();
  }

  function updateChecklistProgress() {
    if (!$.checklist) return;

    var items = $.checklist.querySelectorAll('.checklist-item');
    var checked = $.checklist.querySelectorAll('.checklist-item.checked');

    var total = items.length;
    var done = checked.length;

    var checklistProgress = $.checklist.querySelector(
      '.checklist-progress'
    );
    if (checklistProgress) {
      checklistProgress.textContent = done + '/' + total + ' itens';
    }
  }

  // -----------------------------------------------------------------------
  //  Toggle Previous Answers
  // -----------------------------------------------------------------------
  function togglePreviousAnswers() {
    state.answersVisible = !state.answersVisible;

    if (!$.prevAnswers) return;

    if (state.answersVisible) {
      renderPreviousAnswers();
      $.prevAnswers.classList.add('open');
      if ($.prevAnswersToggle) {
        $.prevAnswersToggle.textContent = 'Ocultar respostas anteriores';
      }
    } else {
      $.prevAnswers.classList.remove('open');
      if ($.prevAnswersToggle) {
        $.prevAnswersToggle.textContent = 'Ver respostas anteriores';
      }
    }
  }

  function renderPreviousAnswers() {
    if (!$.prevAnswers) return;

    var container = $.prevAnswers;
    var phaseLabels = {
      1: 'Descoberta',
      2: 'Definição',
      3: 'Desenvolvimento',
      4: 'Entrega'
    };

    // Clear existing content (keep header if any)
    var header = container.querySelector('h4');
    container.innerHTML = '';
    if (header) container.appendChild(header);

    var hasData = false;

    for (var phaseNum = 1; phaseNum <= state.totalPhases; phaseNum++) {
      var phaseData = state.submittedData['phase_' + phaseNum];
      if (!phaseData || Object.keys(phaseData).length === 0) continue;

      hasData = true;

      var phaseTitle = document.createElement('h5');
      phaseTitle.className = 'mt-4 mb-2';
      phaseTitle.textContent =
        'Fase ' + phaseNum + ': ' + (phaseLabels[phaseNum] || '');
      container.appendChild(phaseTitle);

      for (var key in phaseData) {
        if (phaseData.hasOwnProperty(key) && phaseData[key]) {
          var item = document.createElement('div');
          item.className = 'answer-item';
          var label = key.replace(/_/g, ' ').replace(/\b\w/g, function (c) {
            return c.toUpperCase();
          });
          item.innerHTML =
            '<strong>' + label + '</strong>' + phaseData[key];
          container.appendChild(item);
        }
      }
    }

    if (!hasData) {
      var emptyMsg = document.createElement('p');
      emptyMsg.className = 'text-muted text-sm';
      emptyMsg.textContent =
        'Nenhuma resposta salva ainda. Preencha os campos para ver suas respostas aqui.';
      container.appendChild(emptyMsg);
    }
  }

  // -----------------------------------------------------------------------
  //  Expose wizard API for debugging / external use
  // -----------------------------------------------------------------------
  window.__APPCOPILOT_WIZARD = {
    state: state,
    goToNextPhase: goToNextPhase,
    goToPrevPhase: goToPrevPhase,
    navigateToPhase: navigateToPhase,
    validateCurrentPhase: validateCurrentPhase,
    submitCurrentPhase: submitCurrentPhase,
    getCurrentPhase: function () {
      return state.currentPhase;
    },
    getProgress: function () {
      return Math.round(
        (document.querySelectorAll(selectors.phaseSteps + '.completed')
          .length /
          state.totalPhases) *
          100
      );
    }
  };

})();
