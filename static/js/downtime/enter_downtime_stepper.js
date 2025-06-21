const stepsToCheck = ['modifications', 'engineering', 'science', 'reputation'];
stepsToCheck.forEach(function(step) {
    const $link = $('#downtime-steps-list .nav-link[data-step="' + step + '"]');
    if ($link.length) {
        const hasSlots = $link.data('has-slots');
        if (hasSlots === false || hasSlots === 'False' || hasSlots === 'false') {
            $link.parent().hide();
            $('.downtime-step[data-step="' + step + '"]').hide();
            const idx = steps.indexOf(step);
            if (idx !== -1) {
                steps.splice(idx, 1);
            }
        }
    }
});

// Initialize the first step
showStep(0);

$('.prev-step').on('click', function() {
    if (currentStep > 0) {
        showStep(currentStep - 1);
    }
});

$('.next-step').on('click', function() {
    if (currentStep < steps.length - 1) {
        showStep(currentStep + 1);
    }
});

$('#downtime-steps-list .nav-link').on('click', function(e) {
    e.preventDefault();
    const step = $(this).data('step');
    const stepIndex = steps.indexOf(step);
    if (stepIndex !== -1) {
        showStep(stepIndex);
    }
});

function showStep(stepIndex) {
    $('.downtime-step').hide();
    $('.downtime-step[data-step="' + steps[stepIndex] + '"]').show();
    $('.downtime-step[data-step="submit"]').show(); // Always show submit step
    $('#downtime-steps-list .nav-link').removeClass('active');
    $('#downtime-steps-list .nav-link[data-step="' + steps[stepIndex] + '"]').addClass('active');
    currentStep = stepIndex;
    if (!visitedSteps[steps[stepIndex]]) {
        visitedSteps[steps[stepIndex]] = true;
    }
    updateNavButtons();
    updateStepperBar();
}

function updateNavButtons() {
    $('.prev-step').prop('disabled', currentStep === 0);
    $('.next-step').prop('disabled', currentStep === steps.length - 1);
}

function dirtyStep(step) {
    dirtySteps[step] = true;
    validate();
    updateStepperBar();
}

function updateStepperBar() {
    steps.forEach((step, idx) => {
        const $nav = $('#downtime-steps-list [data-step="' + step + '"]');
        const $icon = $nav.find('.step-status-icon');
        $nav.removeClass('active complete error incomplete');
        $icon.html('').attr('style', '');
        $nav.css('color', '');
        if (idx === currentStep) {
            $nav.addClass('active');
            $nav.css('color', '');
        } else {
            $nav.addClass('complete');
            $icon.html('');
            $nav.css('color', '');
        }
        if (visitedSteps[step]) {
            if (stepErrors[step]) {
                $icon.html('&#10007;').css('color', 'red');
            } else {
                $icon.html('&#10003;').css('color', 'green');
            }
        }
    });
}
