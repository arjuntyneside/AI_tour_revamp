document.addEventListener('DOMContentLoaded', function() {
    var sidebar = document.getElementById('sidebar');
    var mainContent = document.querySelector('.main-content');
    var toggleBtn = document.getElementById('sidebar-toggle');
    var chevron = toggleBtn ? toggleBtn.querySelector('.chevron') : null;

    function updateChevron() {
        if (!chevron) return;
        if (sidebar.classList.contains('collapsed')) {
            chevron.classList.remove('chevron-left');
            chevron.classList.add('chevron-right');
        } else {
            chevron.classList.remove('chevron-right');
            chevron.classList.add('chevron-left');
        }
    }

    if (sidebar && mainContent && toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('sidebar-collapsed');
            updateChevron();
        });
        updateChevron();
    }
}); 