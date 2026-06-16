(function () {
    function toggleCollapse(button) {
        var target = button.getAttribute('data-bs-target');
        if (!target) return;
        var panel = document.querySelector(target);
        if (!panel) return;
        panel.classList.toggle('show');
        button.setAttribute('aria-expanded', panel.classList.contains('show') ? 'true' : 'false');
    }

    document.addEventListener('click', function (event) {
        var button = event.target.closest('[data-bs-toggle="collapse"]');
        if (!button) return;
        toggleCollapse(button);
    });
})();
