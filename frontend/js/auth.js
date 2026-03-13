// js/auth.js

document.addEventListener('DOMContentLoaded', () => {
    // Role Switching Logic
    const roleBtns = document.querySelectorAll('.role-btn');
    const formSections = document.querySelectorAll('.form-section');

    // Parse URL params to select specific role automatically
    const params = new URLSearchParams(window.location.search);
    const requestedRole = params.get('role');
    const requestedMode = params.get('mode');

    if (requestedRole) {
        switchRole(requestedRole);
    }

    if (requestedMode === 'signup') {
        switchRole('merchant'); // default to merchant for signups, or can be dynamic
    }

    roleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const role = e.target.getAttribute('data-role');
            switchRole(role);
        });
    });

    function switchRole(role) {
        // Update Buttons
        roleBtns.forEach(btn => {
            if (btn.getAttribute('data-role') === role) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update Forms
        formSections.forEach(section => {
            if (section.id === `form-${role}`) {
                section.classList.add('active');
            } else {
                section.classList.remove('active');
            }
        });
    }
});

// Customer Tab Switching (Login vs Register)
function switchCustomerTab(tab) {
    const loginSec = document.getElementById('cust-login');
    const regSec = document.getElementById('cust-register');
    const btns = document.querySelectorAll('.cust-tab-btn');

    if (tab === 'login') {
        loginSec.style.display = 'block';
        regSec.style.display = 'none';
        btns[0].classList.add('active');
        btns[1].classList.remove('active');
    } else {
        loginSec.style.display = 'none';
        regSec.style.display = 'block';
        btns[0].classList.remove('active');
        btns[1].classList.add('active');
    }
}

// Dispatcher 2FA Flow Simulation
let dispatcherMfaRequested = false;

function handleDispatcherAuth() {
    const btn = document.getElementById('btn-dispatcher');
    const mfaGroup = document.getElementById('mfaGroup');
    const zoneGroup = document.getElementById('dispatchZoneGroup');

    if (!dispatcherMfaRequested) {
        // Step 1: Show MFA Input
        dispatcherMfaRequested = true;
        mfaGroup.style.display = 'block';
        zoneGroup.style.display = 'none'; // hide zone to make space
        btn.textContent = 'Access Dashboard';
        btn.style.background = '#4CAF50';
    } else {
        // Step 2: Login
        window.location.href = 'dashboard-dispatcher.html';
    }
}
