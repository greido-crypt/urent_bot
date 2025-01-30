document.addEventListener('DOMContentLoaded', function () {
    initMap();
    fadeOutHeader();
    initEventListeners();
});

function initMap() {
    const map = new mapgl.Map('map', {
        center: [37.818508, 55.751797],
        zoom: 15,
        key: '82de0e80-2b53-4d04-b5e8-065a25ccab00',
        style: 'c080bb6a-8134-4993-93a1-5b4d8c36a59b'
    });
}

function fadeOutHeader() {
    setTimeout(() => document.querySelector('.header')?.classList.add('fadeOut'), 2000);
}

function initEventListeners() {
    document.getElementById('scooterInputButton').addEventListener('click', toggleScooterInputMenu);
    const scooterInputMenu = document.getElementById('scooterInputMenu');
    addSwipeDownListener(scooterInputMenu);

    const inputScooter = document.getElementById('inputScooter');
    const getScooterButton = document.getElementById('getScooterButton');
    inputScooter.addEventListener('input', () => toggleGetScooterButton(inputScooter, getScooterButton));
    getScooterButton.addEventListener('click', fetchScooterInfo);

    document.getElementById('settingsButton').addEventListener('click', fetchProfileInfo);
}

function toggleScooterInputMenu() {
    const scooterInputMenu = document.getElementById('scooterInputMenu');
    scooterInputMenu.classList.toggle('open');
}

function addSwipeDownListener(menu) {
    let startY = 0;
    menu.addEventListener('touchstart', e => startY = e.touches[0].clientY);
    menu.addEventListener('touchmove', e => {
        if (e.touches[0].clientY - startY > 50) menu.classList.remove('open');
    });
    menu.addEventListener('touchend', e => {
        if (e.changedTouches[0].clientY - startY > 50) menu.classList.remove('open');
    });
}

function toggleGetScooterButton(inputScooter, getScooterButton) {
    getScooterButton.disabled = !(inputScooter.value.length === 6 && /^\d+$/.test(inputScooter.value));
}

function fetchScooterInfo() {
    const scooterId = document.getElementById('inputScooter').value;
    fetch(`http://127.0.0.1:8137/api/v1/get_scooter_info`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('scooterInputMenu').classList.remove('open');
            displayScooterInfo(data);
        })
        .catch(error => {
            console.error('Error fetching scooter info:', error);
            displayErrorHeader('Ошибка получения информации о самокате');
        });
}

function fetchProfileInfo() {
    fetch(`http://127.0.0.1:8137/api/v1/get_profile`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            displayProfileInfo(data);
        })
        .catch(error => {
            console.error('Error fetching profile info:', error);
            displayErrorHeader('Ошибка получения информации о профиле');
        });
}

function displayScooterInfo(data) {
    removeElementIfExists('scooterMenu');
    const scooterMenu = createScooterMenu(data);
    document.body.appendChild(scooterMenu);
    addSwipeDownListener(scooterMenu);
    scooterMenu.classList.add('open');
}

function displayProfileInfo(data) {
    removeElementIfExists('settingsMenu');
    const settingsMenu = createProfileMenu(data);
    document.body.appendChild(settingsMenu);
    addSwipeDownListener(settingsMenu);
    setTimeout(() => {
        settingsMenu.classList.add('open');
    }, 50);
}

function removeElementIfExists(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

function createScooterMenu(data) {
    const scooterMenu = document.createElement('div');
    scooterMenu.id = 'scooterMenu';
    scooterMenu.classList.add('popup-menu');
    scooterMenu.innerHTML = `
        <div class="popup-handle"></div>
        <div class="popup-content centered">
            <div class="text-content">
                <h3>Меню самоката</h3>
            </div>
            <div id="scooterInfo" class="setting-item">
                <div class="left-section">
                    <img id="scooterIcon" src="${getScooterIcon(data.scooterCharge)}" alt="ScooterIcon">
                    <div id="scooterCharge" class="text-content">
                        <h3>${data.scooterCharge}%</h3>
                    </div>
                </div>
                <div class="right-section">
                    <div id="scooterName" class="text-content">
                        <h3>${data.scooterName}</h3>
                    </div>
                    <div id="scooterId" class="text-content">
                        <h3>${data.scooterId}</h3>
                    </div>
                </div>
            </div>
            <div id="startRideInfo" class="setting-item">
                <button id="startRideButton">${data.startRideButton}</button>
            </div>
            <div id="autoEndRide" class="setting-item">
                <img src="cpsdk_ic_no_banks_apps.png" alt="ScooterIcon">
                <div id="maxRideInMinutes" class="text-content">
                    <h3>${data.maxRideInMinutes}</h3>
                </div>
            </div>
            <div class="setting-item">
                <button id="autoEndRideButton">Отключить</button>
            </div>
        </div>
    `;
    return scooterMenu;
}

function createProfileMenu(data) {
    const settingsMenu = document.createElement('div');
    settingsMenu.id = 'settingsMenu';
    settingsMenu.classList.add('popup-menu');
    settingsMenu.innerHTML = `
        <div class="popup-handle"></div>
        <div class="popup-content">
            <div id="phoneNumber" class="setting-item">
                <img src="https://img.icons8.com/?size=100&id=14736&format=png&color=804aff" alt="Profile Icon">
                <div class="text-content">
                    <h3>Профиль</h3>
                    <p>${data.phoneNumber}</p>
                </div>
            </div>
            <div id="balance" class="setting-item">
                <img src="https://img.icons8.com/?size=100&id=7991&format=png&color=804aff" alt="Wallet Icon">
                <div class="text-content">
                    <h3>Кошелек </h3>
                    <p>${data.balance}<span class="badge"></span></p>
                </div>
            </div>
            <div id="historyRide" class="setting-item">
                <button id="historyRideButton">
                    <img src="https://img.icons8.com/?size=100&id=zfvfYFgHI0ls&format=png&color=804aff" alt="History Icon">
                    <h3>История поездок</h3>
                </button>
            </div>
            <div id="activePromoAction" class="setting-item">
                <img src="https://img.icons8.com/?size=100&id=7697&format=png&color=804aff" alt="Discount Icon">
                <div class="text-content">
                    <h3>Активная скидка</h3>
                    <p>${data.activePromoAction}</p>
                </div>
            </div>
            
            <div id="mtsPremium" class="setting-item">
                <button id="mtsPremiumButton">
                    <p>Бесплатный старт, кешбэк 15% и преимущества МТС Premium</p>
                    <img src="top.png" alt="Advert Icon">
                </button>
            </div>
            
            <div id="instructions" class="setting-item">
                <button id="instructionButton">
                    <h3>Инструкция</h3>          
                    <img src="https://img.icons8.com/?size=100&id=2908&format=png&color=FFFFFF" alt="Instruction Icon">
                </button>
            </div>
        </div>
    `;

    settingsMenu.querySelector('#mtsPremiumButton').addEventListener('click', () => {
        window.location.href = 'https://teletype.in/@shadow1ch/mts_premium';
    });

    settingsMenu.querySelector('#instructionButton').addEventListener('click', () => {
        window.location.href = 'https://teletype.in/@shadow1ch/shadow_urent';
    });

    return settingsMenu;
}

function getScooterIcon(scooterCharge) {
    if (scooterCharge <= 20) {
        return 'ic_scooter_charge_ultra_low.png';
    } else if (scooterCharge <= 40) {
        return 'ic_scooter_charge_low.png';
    } else if (scooterCharge <= 60) {
        return 'ic_scooter_charge_medium.png';
    } else if (scooterCharge <= 80) {
        return 'ic_scooter_charge_high.png';
    } else {
        return 'ic_scooter_charge_full.png';
    }
}

function displayErrorHeader(message) {
    const header = document.querySelector('.header');
    header.classList.remove('fadeOut');
    header.id = "errorHeader";
    header.innerHTML = `<img src="cpsdk_ic_failure.png" alt="error icon"><span>${message}</span>`;
    header.classList.add('fadeIn');
    setTimeout(() => {
        header.classList.remove('fadeIn');
        header.classList.add('fadeOut');
    }, 1500);
}
