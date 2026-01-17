// --- 遊戲常數 ---
const SCREEN_WIDTH = 800;
const SCREEN_HEIGHT = 600;

// 顏色定義
const COLOR_YELLOW = "#FFFF00"; // 金幣 (備用)
const COLOR_SILVER = "#C0C0C0"; // 銀幣 (備用)
const COLOR_RED = "#FF0000";    // 炸彈
const COLOR_BLUE = "#0088FF";   // 磁鐵
const COLOR_CYAN = "#00FFFF";   // 護盾

const PLAYER_SIZE = 50; 

// FPS 優化設定 (135 FPS)
const TARGET_FPS = 135;
const FRAME_INTERVAL = 1000 / TARGET_FPS;
const SCALE_FACTOR = 60 / TARGET_FPS;

// 縮放後的速度
const PLAYER_SPEED = 7 * SCALE_FACTOR;
const COIN_SPEED = 5 * SCALE_FACTOR;

// 物理
let GAME_GRAVITY = 0.5 * SCALE_FACTOR;
let GAME_JUMP_FORCE = 15 * SCALE_FACTOR;

// 玩家狀態
let wallet = 0; 
let particles = []; 
let upgradeLevels = {
    multiplier: 0,
    luck: 0,
    goldChance: 0 // 新增：金幣機率等級
};

// 遊戲內暫時狀態
let activePowerups = {
    magnet: 0, // 剩餘幀數
    shield: false
};

// 升級設定
const UPGRADES = {
    multiplier: {
        name: "金幣倍率 (Coin Multiplier)",
        desc: "增加結算時獲得的金幣",
        levels: [1.0, 1.2, 1.5, 2.0, 3.0],
        costs: [100, 250, 500, 1000, "MAX"]
    },
    luck: {
        name: "幸運值 (Luck)",
        desc: "增加強力道具掉落機率",
        levels: [0.005, 0.02, 0.04, 0.06, 0.1], // 掉落機率
        costs: [150, 300, 600, 1200, "MAX"]
    },
    goldChance: {
        name: "鍊金術 (Gold Rush)",
        desc: "增加黃金硬幣出現機率",
        levels: [0.01, 0.05, 0.10, 0.20, 0.40], // 初始 1% -> 最高 40%
        costs: [200, 400, 800, 1600, "MAX"]
    }
};

// 造型資料
const SKINS = [
    { id: 'default', name: '經典白', color: '#FFFFFF', price: 0, owned: true },
    { id: 'blue', name: '賽博藍', color: '#00FFFF', price: 50, owned: false },
    { id: 'pink', name: '霓虹粉', color: '#FF00FF', price: 100, owned: false },
    { id: 'gold', name: '土豪金', color: '#FFD700', price: 200, owned: false },
    { id: 'matrix', name: '駭客綠', color: '#00FF00', price: 300, owned: false },
    { id: 'red', name: '危險紅', color: '#FF4444', price: 500, owned: false }
];
let currentSkinId = 'default';

const COIN_SIZE = 50;
const COIN_RADIUS = COIN_SIZE / 2;
const MIN_SEPARATION = 80;

// --- 資源管理器 (Resource Manager) ---
const ResourceManager = {
    assets: {
        gold: [],
        silver: []
    },
    settings: {
        goldFolder: "assets/Coin Animation_sprites/",
        goldPrefix: "coin", 
        silverFolder: "assets/Silver_sprites/",
        silverPrefix: "silver", // 假設銀幣檔名為 silver1.png, silver2.png...
        count: 6 // 假設張數相同
    },

    init() {
        // 載入黃金硬幣
        for (let i = 1; i <= this.settings.count; i++) {
            const img = new Image();
            img.src = `${this.settings.goldFolder}${this.settings.goldPrefix}${i}.png`;
            this.assets.gold.push(img);
        }
        // 載入白銀硬幣
        for (let i = 1; i <= this.settings.count; i++) {
            const img = new Image();
            img.src = `${this.settings.silverFolder}${this.settings.silverPrefix}${i}.png`;
            this.assets.silver.push(img);
        }
    },

    // 取得指定幀的金幣圖片 (新增檢查：確保圖片已載入且有效)
    getGoldSprite(frameIndex) {
        if (this.assets.gold.length === 0) return null;
        const img = this.assets.gold[frameIndex % this.assets.gold.length];
        return (img.complete && img.naturalWidth > 0) ? img : null;
    },

    getSilverSprite(frameIndex) {
        if (this.assets.silver.length === 0) return null;
        const img = this.assets.silver[frameIndex % this.assets.silver.length];
        return (img.complete && img.naturalWidth > 0) ? img : null;
    },

    // 檢查資源是否準備就緒 (只要有一張圖有效就算 Ready，避免全黑)
    isReady() {
        const hasGold = this.assets.gold.some(img => img.complete && img.naturalWidth > 0);
        const hasSilver = this.assets.silver.some(img => img.complete && img.naturalWidth > 0);
        return hasGold || hasSilver; 
    },
    
    getFrameCount() {
        return this.settings.count;
    }
};

// 初始化資源
ResourceManager.init();

// --- DOM 元素 ---
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score-display');
const walletElement = document.getElementById('wallet-amount');
const multiplierElement = document.getElementById('multiplier-display');
const shieldElement = document.getElementById('shield-display');

const shopWalletElement = document.getElementById('shop-wallet');
const finalScoreElement = document.getElementById('final-score');
const earnedCoinsElement = document.getElementById('earned-coins');
const endMultElement = document.getElementById('end-mult');
const gameOverScreen = document.getElementById('game-over-screen');

const skinContainer = document.getElementById('skin-container');
const upgradeContainer = document.getElementById('upgrade-container');

// UI Sliders
const gravitySlider = document.getElementById('gravity-slider');
const jumpSlider = document.getElementById('jump-slider');
const gravVal = document.getElementById('grav-val');
const jumpVal = document.getElementById('jump-val');
const previewTriggerBtn = document.getElementById('preview-trigger-btn');
const presetBtns = document.querySelectorAll('.preset-btn');

let isModalOpen = false;
let isPaused = false;
let score = 0;
let isGameOver = false;
let gameIntervalId;

const keys = { ArrowLeft: false, ArrowRight: false };

// --- 粒子特效 ---
class Particle {
    constructor(x, y, color) {
        this.x = x;
        this.y = y;
        this.color = color;
        this.size = Math.random() * 5 + 3;
        this.speedX = (Math.random() * 6 - 3) * SCALE_FACTOR;
        this.speedY = (Math.random() * 6 - 3) * SCALE_FACTOR;
        this.life = 1.0; 
        this.decay = (Math.random() * 0.02 + 0.02) * SCALE_FACTOR;
    }
    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.life -= this.decay;
        this.size *= 0.98;
    }
    draw(ctx) {
        ctx.save();
        ctx.globalAlpha = Math.max(0, this.life);
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }
}

function createExplosion(x, y, color) {
    for (let i = 0; i < 12; i++) {
        particles.push(new Particle(x, y, color));
    }
}

// --- 類別定義 ---
class Player {
    constructor() {
        this.width = PLAYER_SIZE;
        this.height = PLAYER_SIZE;
        this.reset();
    }

    reset() {
        this.x = (SCREEN_WIDTH / 2) - (this.width / 2);
        this.y = SCREEN_HEIGHT - this.height;
        this.dy = 0;
        this.onGround = true;
        this.trail = []; 
        this.blinkTimer = 0; 
        activePowerups.magnet = 0;
        activePowerups.shield = false;
        updateStatusUI();
    }

    jump() {
        if (this.onGround && !isPaused) {
            this.dy = -GAME_JUMP_FORCE;
            this.onGround = false;
            this.blinkTimer = 45; 
        }
    }

    update() {
        if (isPaused) return;

        // 磁鐵計時器
        if (activePowerups.magnet > 0) activePowerups.magnet--;

        // 殘影
        if (Math.abs(this.dy) > 0.1 || keys.ArrowLeft || keys.ArrowRight) {
             this.trail.push({x: this.x, y: this.y, alpha: 0.5});
        }
        if (this.trail.length > 20) this.trail.shift();
        this.trail.forEach(t => t.alpha -= 0.02);
        this.trail = this.trail.filter(t => t.alpha > 0);

        if (this.blinkTimer > 0) this.blinkTimer--;

        if (keys.ArrowLeft) this.x -= PLAYER_SPEED;
        if (keys.ArrowRight) this.x += PLAYER_SPEED;

        this.dy += GAME_GRAVITY;
        this.y += this.dy;

        const groundLevel = SCREEN_HEIGHT - this.height;
        if (this.y >= groundLevel) {
            this.y = groundLevel;
            this.dy = 0;
            this.onGround = true;
            this.blinkTimer = 0; 
        }

        if (this.x < 0) this.x = 0;
        if (this.x + this.width > SCREEN_WIDTH) this.x = SCREEN_WIDTH - this.width;
    }

    draw() {
        const skin = SKINS.find(s => s.id === currentSkinId);
        const skinColor = skin ? skin.color : '#FFFFFF';
        
        // 繪製殘影
        this.trail.forEach(t => {
            ctx.save();
            ctx.globalAlpha = t.alpha * 0.4;
            ctx.fillStyle = skinColor;
            ctx.fillRect(t.x, t.y, this.width, this.height);
            ctx.restore();
        });

        // 繪製本體
        ctx.fillStyle = skinColor;
        ctx.fillRect(this.x, this.y, this.width, this.height);
        
        // 繪製眼睛
        ctx.fillStyle = '#000';
        let eyeY = (this.blinkTimer > 0) ? 15 : 12;
        let eyeH = (this.blinkTimer > 0) ? 2 : 6;
        
        if (keys.ArrowRight) {
            ctx.fillRect(this.x + 35, this.y + eyeY, 6, eyeH); 
        } else if (keys.ArrowLeft) {
            ctx.fillRect(this.x + 10, this.y + eyeY, 6, eyeH); 
        } else {
            ctx.fillRect(this.x + 12, this.y + eyeY, 6, eyeH); 
            ctx.fillRect(this.x + 32, this.y + eyeY, 6, eyeH);
        }

        // 繪製護盾特效
        if (activePowerups.shield) {
            ctx.save();
            ctx.strokeStyle = COLOR_CYAN;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(this.x + this.width/2, this.y + this.height/2, this.width/1.2, 0, Math.PI * 2);
            ctx.stroke();
            ctx.globalAlpha = 0.2;
            ctx.fillStyle = COLOR_CYAN;
            ctx.fill();
            ctx.restore();
        }

        // 繪製磁鐵特效 (頭頂小標示)
        if (activePowerups.magnet > 0) {
             ctx.fillStyle = COLOR_BLUE;
             ctx.beginPath();
             ctx.arc(this.x + this.width/2, this.y - 15, 5, 0, Math.PI*2);
             ctx.fill();
        }
    }

    getRect() {
        return { left: this.x, right: this.x + this.width, top: this.y, bottom: this.y + this.height };
    }
}

class FallingItem {
    constructor(type) {
        this.type = type || 'silver_coin'; // 預設現在是銀幣
        this.width = COIN_SIZE;
        this.height = COIN_SIZE;
        this.radius = COIN_RADIUS;
        this.rect = { x: 0, y: -COIN_SIZE };

        // 動畫狀態
        this.currentFrame = 0;
        this.frameTimer = 0;
        this.frameInterval = Math.floor(TARGET_FPS * 0.5); // Animation interval ~500ms
    }

    reset(others) {
        // 恢復原始類型
        if (this.baseType === undefined) {
            // 如果初始就是 coin，我們把它標記為 'coin_slot'，表示它是可以變化的硬幣位
            this.baseType = (this.type === 'coin' || this.type === 'silver_coin' || this.type === 'gold_coin') ? 'coin_slot' : this.type;
        }
        
        // 每次重置邏輯
        if (this.baseType === 'coin_slot') {
            let rand = Math.random();
            let luck = UPGRADES.luck.levels[upgradeLevels.luck];
            
            // 1. 決定是否為強力道具
            if (rand < luck) {
                this.type = Math.random() < 0.5 ? 'magnet' : 'shield';
            } else {
                // 2. 決定是金幣還是銀幣
                let goldChance = UPGRADES.goldChance.levels[upgradeLevels.goldChance];
                this.type = Math.random() < goldChance ? 'gold_coin' : 'silver_coin';
            }
        } else {
            this.type = this.baseType; // 炸彈保持炸彈
        }

        // 重置動畫幀
        this.currentFrame = Math.floor(Math.random() * ResourceManager.getFrameCount());

        // 位置重置
        let attempts = 0;
        let success = false;
        while (attempts < 50) {
            const newX = Math.floor(Math.random() * (SCREEN_WIDTH - COIN_SIZE));
            let isSeparated = true;
            if (others) {
                for (let other of others) {
                    if (other === this) continue;
                    if (Math.abs(newX - other.rect.x) < MIN_SEPARATION) {
                        isSeparated = false;
                        break;
                    }
                }
            }
            if (isSeparated) {
                this.rect.x = newX;
                this.rect.y = -Math.floor(Math.random() * 400) - COIN_SIZE;
                success = true;
                break;
            }
            attempts++;
        }
        if (!success) {
            this.rect.x = Math.floor(Math.random() * (SCREEN_WIDTH - COIN_SIZE));
            this.rect.y = -100;
        }
    }

    update() {
        if (isPaused) return;

        const isCoin = (this.type === 'gold_coin' || this.type === 'silver_coin');

        // 金幣動畫邏輯
        if (isCoin) {
            this.frameTimer++;
            if (this.frameTimer >= this.frameInterval) {
                this.frameTimer = 0;
                this.currentFrame = (this.currentFrame + 1) % ResourceManager.getFrameCount();
            }
        }

        // 磁鐵效果
        if (isCoin && activePowerups.magnet > 0 && this.rect.y > 0 && this.rect.y < SCREEN_HEIGHT) {
            let dx = player.x - this.rect.x;
            let dy = player.y - this.rect.y;
            let dist = Math.sqrt(dx*dx + dy*dy);
            
            this.rect.x += (dx / dist) * 10 * SCALE_FACTOR;
            this.rect.y += (dy / dist) * 10 * SCALE_FACTOR;
        } else {
            this.rect.y += COIN_SPEED;
        }

        if (this.rect.y > SCREEN_HEIGHT) {
            if (isCoin) {
                score = Math.max(0, score - 5);
                updateScore();
            }
            this.reset(allItems);
        }
    }

    draw() {
        const isCoin = (this.type === 'gold_coin' || this.type === 'silver_coin');
        let img = null;

        // 嘗試獲取圖片
        if (isCoin) {
            if (this.type === 'gold_coin') {
                img = ResourceManager.getGoldSprite(this.currentFrame);
            } else {
                img = ResourceManager.getSilverSprite(this.currentFrame);
            }
        }

        // 如果有有效圖片，繪製圖片
        if (img) {
            ctx.drawImage(img, this.rect.x, this.rect.y, this.width, this.height);
        } else {
            // 否則繪製圓形 (Fallback)
            ctx.beginPath();
            const cx = this.rect.x + this.radius;
            const cy = this.rect.y + this.radius;
            
            let color = COLOR_YELLOW;
            let text = "";

            if (this.type === 'fake') color = COLOR_RED;
            else if (this.type === 'magnet') { color = COLOR_BLUE; text = "M"; }
            else if (this.type === 'shield') { color = COLOR_CYAN; text = "S"; }
            else if (this.type === 'gold_coin') color = COLOR_YELLOW;
            else if (this.type === 'silver_coin') color = COLOR_SILVER;

            ctx.fillStyle = color;
            ctx.arc(cx, cy, this.radius, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.beginPath();
            ctx.arc(cx - 8, cy - 8, 8, 0, Math.PI * 2);
            ctx.fillStyle = "rgba(255,255,255,0.4)";
            ctx.fill();

            if (text) {
                ctx.fillStyle = "#fff";
                ctx.font = "bold 24px Arial";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(text, cx, cy);
            }
        }
    }
}

// --- 實例化 ---
const player = new Player();
// 調整初始化：預設為 coin，會自動在 reset 時轉為 gold/silver
const coin1 = new FallingItem('coin');
const coin2 = new FallingItem('coin');
const fake1 = new FallingItem('fake');
const fake2 = new FallingItem('fake');
const fake3 = new FallingItem('fake');

const allItems = [coin1, coin2, fake1, fake2, fake3];

allItems.forEach(item => item.reset(allItems));

// --- UI 與設定邏輯 ---

function setModalState(isOpen, modalId) {
    isModalOpen = isOpen;
    const modal = document.getElementById(modalId);
    
    if (isOpen) {
        document.body.classList.add('modal-open');
        modal.classList.add('active');
        isPaused = true;
    } else {
        document.body.classList.remove('modal-open');
        if (modal) modal.classList.remove('active');
        if (!isGameOver) isPaused = false;
    }
}

function toggleSettings() {
    const shop = document.getElementById('shop-modal');
    if (shop.classList.contains('active')) return;
    const settings = document.getElementById('settings-modal');
    const isActive = settings.classList.contains('active');
    setModalState(!isActive, 'settings-modal');
}

// --- 商店系統邏輯 ---
let currentShopTab = 'skins';

function openShop() {
    switchShopTab('skins'); // 預設打開造型
    setModalState(true, 'shop-modal');
    updateShopUI();
}

function closeShop() {
    setModalState(false, 'shop-modal');
}

function switchShopTab(tab) {
    currentShopTab = tab;
    
    // UI 更新
    document.querySelectorAll('.shop-tab').forEach(b => b.classList.remove('active'));
    if (tab === 'skins') document.querySelector("button[onclick=\"switchShopTab('skins')\"]").classList.add('active');
    if (tab === 'upgrades') document.querySelector("button[onclick=\"switchShopTab('upgrades')\"]").classList.add('active');

    document.getElementById('tab-skins').classList.toggle('hidden', tab !== 'skins');
    document.getElementById('tab-upgrades').classList.toggle('hidden', tab !== 'upgrades');

    updateShopUI();
}

function updateShopUI() {
    shopWalletElement.textContent = wallet;
    if (currentShopTab === 'skins') renderSkins();
    else renderUpgrades();
}

// 造型邏輯
function buySkin(id) {
    const skin = SKINS.find(s => s.id === id);
    if (skin && !skin.owned && wallet >= skin.price) {
        wallet -= skin.price;
        skin.owned = true;
        updateWalletDisplay();
        updateShopUI();
    }
}
function equipSkin(id) {
    const skin = SKINS.find(s => s.id === id);
    if (skin && skin.owned) {
        currentSkinId = id;
        updateShopUI();
    }
}
function renderSkins() {
    skinContainer.innerHTML = '';
    SKINS.forEach(skin => {
        const card = document.createElement('div');
        card.className = `skin-card ${skin.owned ? 'owned' : ''} ${currentSkinId === skin.id ? 'equipped' : ''}`;
        card.onclick = () => skin.owned ? equipSkin(skin.id) : buySkin(skin.id);

        const statusHtml = currentSkinId === skin.id 
            ? '<div class="skin-status">已裝備</div>' 
            : (skin.owned ? '<div class="skin-status" style="color:#aaa;">已擁有</div>' : `<div class="skin-price ${wallet >= skin.price ? 'affordable' : ''}">💰 ${skin.price}</div>`);

        card.innerHTML = `
            <div class="skin-preview" style="background-color: ${skin.color}"></div>
            <div class="skin-name">${skin.name}</div>
            <div class="skin-info">${statusHtml}</div>
        `;
        skinContainer.appendChild(card);
    });
}

// 升級邏輯
function buyUpgrade(type) {
    const upg = UPGRADES[type];
    const currentLvl = upgradeLevels[type];
    const cost = upg.costs[currentLvl];

    if (cost !== "MAX" && wallet >= cost) {
        wallet -= cost;
        upgradeLevels[type]++;
        updateWalletDisplay();
        updateStatusUI(); // 更新倍率顯示
        updateShopUI();
    }
}

function renderUpgrades() {
    upgradeContainer.innerHTML = '';
    Object.keys(UPGRADES).forEach(key => {
        const upg = UPGRADES[key];
        const lvl = upgradeLevels[key];
        const cost = upg.costs[lvl];
        const val = upg.levels[lvl];
        const nextVal = upg.levels[lvl+1];
        
        const card = document.createElement('div');
        card.className = 'upgrade-card';

        let btnHtml = '';
        if (cost === "MAX") {
            btnHtml = `<button class="upgrade-btn maxed">MAX</button>`;
        } else {
            const canBuy = wallet >= cost;
            btnHtml = `<button class="upgrade-btn ${canBuy ? 'can-buy' : ''}" onclick="buyUpgrade('${key}')">
                💰 ${cost}<br><span style="font-size:12px">升級</span>
            </button>`;
        }

        let valDisplay;
        if (key === 'multiplier') valDisplay = `x${val}`;
        else if (key === 'goldChance') valDisplay = `${(val*100).toFixed(0)}%`;
        else valDisplay = `${(val*100).toFixed(1)}%`;

        let nextDisplay = "MAX";
        if (nextVal) {
            if (key === 'multiplier') nextDisplay = `x${nextVal}`;
            else if (key === 'goldChance') nextDisplay = `${(nextVal*100).toFixed(0)}%`;
            else nextDisplay = `${(nextVal*100).toFixed(1)}%`;
        }

        card.innerHTML = `
            <div class="upgrade-info">
                <h3>${upg.name} <span style="font-size:14px;color:#aaa;">(Lv.${lvl+1})</span></h3>
                <p>${upg.desc}</p>
                <p style="color:#ffcc00; margin-top:5px;">當前: ${valDisplay} ${nextVal !== "MAX" ? '➜ <span style="color:#8f8">'+nextDisplay+'</span>' : ''}</p>
            </div>
            ${btnHtml}
        `;
        upgradeContainer.appendChild(card);
    });
}

function updateWalletDisplay() {
    walletElement.textContent = wallet;
    shopWalletElement.textContent = wallet;
}

function updateStatusUI() {
    // 倍率
    const mult = UPGRADES.multiplier.levels[upgradeLevels.multiplier];
    multiplierElement.textContent = `x${mult}`;
    
    // 護盾
    if (activePowerups.shield) shieldElement.classList.remove('hidden');
    else shieldElement.classList.add('hidden');
}

// --- 預設與滑桿邏輯 (保持不變) ---
const PRESETS = {
    'easy': { gravity: 0.3 * SCALE_FACTOR, jump: 12 * SCALE_FACTOR },
    'medium': { gravity: 0.5 * SCALE_FACTOR, jump: 15 * SCALE_FACTOR },
    'hard': { gravity: 0.9 * SCALE_FACTOR, jump: 22 * SCALE_FACTOR }
};

function applyPreset(level) {
    const p = PRESETS[level];
    if (!p) return;
    GAME_GRAVITY = p.gravity;
    GAME_JUMP_FORCE = p.jump;
    gravitySlider.value = GAME_GRAVITY / SCALE_FACTOR;
    jumpSlider.value = GAME_JUMP_FORCE / SCALE_FACTOR;
    gravVal.textContent = (GAME_GRAVITY / SCALE_FACTOR).toFixed(1);
    jumpVal.textContent = (GAME_JUMP_FORCE / SCALE_FACTOR).toFixed(0);
    presetBtns.forEach(btn => btn.classList.remove('active'));
    const btns = Array.from(presetBtns);
    const activeBtn = btns.find(b => b.getAttribute('onclick').includes(level));
    if (activeBtn) activeBtn.classList.add('active');
    setTimeout(() => previewTriggerBtn.click(), 100);
}

function updatePhysicsFromSlider() {
    GAME_GRAVITY = parseFloat(gravitySlider.value) * SCALE_FACTOR;
    GAME_JUMP_FORCE = parseInt(jumpSlider.value) * SCALE_FACTOR;
    gravVal.textContent = gravitySlider.value;
    jumpVal.textContent = jumpSlider.value;
    presetBtns.forEach(btn => btn.classList.remove('active'));
}

gravitySlider.addEventListener('input', updatePhysicsFromSlider);
jumpSlider.addEventListener('input', updatePhysicsFromSlider);

// --- 預覽邏輯 (保持不變) ---
const previewCanvas = document.getElementById('previewCanvas');
const pCtx = previewCanvas.getContext('2d');
let previewPlayer = { y: 200, dy: 0, size: 30, groundY: 210, onGround: true };
let previewMaxHeight = 210; 

previewTriggerBtn.addEventListener('click', () => {
    if (previewPlayer.onGround) {
        previewPlayer.dy = -GAME_JUMP_FORCE;
        previewPlayer.onGround = false;
        previewMaxHeight = previewPlayer.groundY;
    }
});

let previewIntervalId;
function previewUpdate() {
    pCtx.fillStyle = '#111';
    pCtx.fillRect(0, 0, previewCanvas.width, previewCanvas.height);
    pCtx.strokeStyle = '#444';
    pCtx.beginPath();
    pCtx.moveTo(0, previewPlayer.groundY + previewPlayer.size);
    pCtx.lineTo(previewCanvas.width, previewPlayer.groundY + previewPlayer.size);
    pCtx.stroke();
    if (!previewPlayer.onGround) {
        previewPlayer.dy += GAME_GRAVITY;
        previewPlayer.y += previewPlayer.dy;
    }
    if (previewPlayer.y >= previewPlayer.groundY) {
        previewPlayer.y = previewPlayer.groundY;
        previewPlayer.dy = 0;
        previewPlayer.onGround = true;
    } else {
        previewPlayer.onGround = false;
    }
    if (previewPlayer.y < previewMaxHeight) previewMaxHeight = previewPlayer.y;
    if (previewMaxHeight < previewPlayer.groundY) {
        pCtx.strokeStyle = 'rgba(255, 50, 50, 0.7)';
        pCtx.setLineDash([5, 5]);
        pCtx.beginPath();
        pCtx.moveTo(0, previewMaxHeight);
        pCtx.lineTo(previewCanvas.width, previewMaxHeight);
        pCtx.stroke();
        pCtx.setLineDash([]);
        pCtx.fillStyle = 'rgba(255, 50, 50, 0.7)';
        pCtx.font = "12px monospace";
        pCtx.fillText(Math.round(previewPlayer.groundY - previewMaxHeight), 5, previewMaxHeight - 5);
    }
    const skin = SKINS.find(s => s.id === currentSkinId);
    pCtx.fillStyle = skin ? skin.color : '#fff';
    pCtx.fillRect((previewCanvas.width / 2) - (previewPlayer.size / 2), previewPlayer.y, previewPlayer.size, previewPlayer.size);
}
clearInterval(previewIntervalId);
previewIntervalId = setInterval(previewUpdate, FRAME_INTERVAL);

// --- 主遊戲邏輯 ---
function checkCollisions() {
    if (isPaused) return;
    const pRect = player.getRect();
    
    // 需倒序遍歷以方便刪除或修改
    for (let i = allItems.length - 1; i >= 0; i--) {
        let item = allItems[i];
        const iRect = { left: item.rect.x, right: item.rect.x + item.width, top: item.rect.y, bottom: item.rect.y + item.height };
        
        if (pRect.left < iRect.right && pRect.right > iRect.left && pRect.top < iRect.bottom && pRect.bottom > iRect.top) {
            // 發生碰撞
            
            if (item.type === 'silver_coin' || item.type === 'gold_coin') {
                // 銀幣 10 分, 金幣 50 分
                const points = (item.type === 'gold_coin') ? 50 : 10;
                const color = (item.type === 'gold_coin') ? COLOR_YELLOW : COLOR_SILVER;
                
                score += points;
                createExplosion(item.rect.x + item.width/2, item.rect.y + item.height/2, color);
                updateScore();
                item.reset(allItems);
            } 
            else if (item.type === 'magnet') {
                activePowerups.magnet = 600; // 約 4-5 秒 (135FPS)
                createExplosion(item.rect.x + item.width/2, item.rect.y + item.height/2, COLOR_BLUE);
                item.reset(allItems);
            }
            else if (item.type === 'shield') {
                activePowerups.shield = true;
                updateStatusUI();
                createExplosion(item.rect.x + item.width/2, item.rect.y + item.height/2, COLOR_CYAN);
                item.reset(allItems);
            }
            else if (item.type === 'fake') {
                if (activePowerups.shield) {
                    // 護盾抵擋
                    activePowerups.shield = false;
                    updateStatusUI();
                    createExplosion(item.rect.x + item.width/2, item.rect.y + item.height/2, "#FFFFFF"); // 白光特效
                    item.reset(allItems); // 炸彈消失
                } else {
                    gameOver();
                }
            }
        }
    }
}

function updateScore() {
    scoreElement.textContent = `Score: ${score}`;
}

function gameLoop() {
    if (isGameOver) return;
    
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
    
    particles.forEach((p, index) => {
        p.update();
        p.draw(ctx);
        if (p.life <= 0) particles.splice(index, 1);
    });

    player.update();
    allItems.forEach(item => item.update());
    checkCollisions();
    player.draw();
    allItems.forEach(item => item.draw());
    
    if (isPaused) {
        ctx.fillStyle = "rgba(0, 0, 0, 0.3)";
        ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
        ctx.fillStyle = "white";
        ctx.font = "30px Arial";
        ctx.textAlign = "center";
        ctx.fillText("PAUSED", SCREEN_WIDTH/2, SCREEN_HEIGHT/2);
        ctx.textAlign = "left";
    }
}

function gameOver() {
    isGameOver = true;
    clearInterval(gameIntervalId);
    
    // 計算金幣倍率
    const mult = UPGRADES.multiplier.levels[upgradeLevels.multiplier];
    const earned = Math.floor(score * mult);
    wallet += earned;
    
    updateWalletDisplay();

    finalScoreElement.textContent = score;
    earnedCoinsElement.textContent = earned;
    endMultElement.textContent = mult; // 顯示倍率
    gameOverScreen.style.display = 'flex';
}

window.resetGame = function() {
    score = 0;
    updateScore();
    isGameOver = false;
    isPaused = false;
    gameOverScreen.style.display = 'none';
    
    document.body.classList.remove('modal-open');
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));

    player.reset();
    particles = []; 
    allItems.forEach(item => { item.rect.y = -200; });
    allItems.forEach(item => item.reset(allItems));
    
    clearInterval(gameIntervalId);
    gameIntervalId = setInterval(gameLoop, FRAME_INTERVAL);
};

// --- 輸入監聽 ---
window.addEventListener('keydown', (e) => {
    if (document.body.classList.contains('modal-open')) {
        if (e.key === 'Escape') {
             setModalState(false, 'settings-modal');
             setModalState(false, 'shop-modal');
        }
        return;
    }

    if (e.key === 'ArrowLeft') keys.ArrowLeft = true;
    if (e.key === 'ArrowRight') keys.ArrowRight = true;
    if (e.key === ' ' || e.key === 'ArrowUp') {
        player.jump();
        e.preventDefault();
    }
    if (e.key === 'Escape') toggleSettings();
});

window.addEventListener('keyup', (e) => {
    if (e.key === 'ArrowLeft') keys.ArrowLeft = false;
    if (e.key === 'ArrowRight') keys.ArrowRight = false;
});

updateWalletDisplay();
updateStatusUI();
clearInterval(gameIntervalId);
gameIntervalId = setInterval(gameLoop, FRAME_INTERVAL);