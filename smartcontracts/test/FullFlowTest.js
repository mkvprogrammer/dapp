// test/FullFlowTest.js
const { expect } = require("chai");     // для проверки результатов
const { ethers } = require("hardhat");  // для полного управления блокчейном и контрактами во время тестов

describe("University Auction System - Full Flow", function () {
    let token, registry, auction;
    let admin, organizer, student1, student2, student3;

    // запускается перед каждым тестом (it)
    // создаёт «чистый лист» для каждого теста, чтобы они не зависели друг от друга
    beforeEach(async function () {
        // берёт первые 5 аккаунтов и раскладывает их по переменным
        [admin, organizer, student1, student2, student3] = await ethers.getSigners();
        
        // 1. Сначала деплоим Registry (не требует аргументов)
        const Registry = await ethers.getContractFactory("ProjectRegistry");
        registry = await Registry.deploy();
        await registry.waitForDeployment();

        // Деплой контрактов
        // находит скомпилированный Solidity-контракт по его имени и 
        // подготавливает его к отправке в сеть
        const Token = await ethers.getContractFactory("UniversityToken");
        token = await Token.deploy(await registry.getAddress()); // ПЕРЕДАЕМ АДРЕС РЕЕСТРА
        await token.waitForDeployment();

        const Auction = await ethers.getContractFactory("AuctionManager");
        auction = await Auction.deploy(
            await token.getAddress(),
            await registry.getAddress()
        );
        await auction.waitForDeployment();

        // Настройка ролей
        const ADMIN_ROLE = await token.DEFAULT_ADMIN_ROLE();
        await token.grantRole(ADMIN_ROLE, await auction.getAddress()); // Для штрафов

        const ORG_ROLE = await registry.ORGANIZER_ROLE();
        // Чтобы контракт Аукциона мог списывать токены у студентов в качестве штрафа,
        // контракт Токена должен явно выдать ему права администратора
        await registry.grantRole(ORG_ROLE, organizer.address);
        await auction.grantRole(ORG_ROLE, organizer.address);
        await token.grantRole(ORG_ROLE, organizer.address); // Чтобы организатор мог вызывать mint()

        // Если студенты должны создавать аукционы:
        const USER_ROLE = await auction.USER_ROLE();
        await auction.grantRole(USER_ROLE, student1.address);
    });

    async function setupProjectAndAuction({
        projectName = "Mathematics",
        refundRate = 9000,
        penalties = [0, 2000, 3000, 5000], // в basis points!
        auctionName = "Lab #1",
        slots = 2
    } = {}) {
        await registry.connect(organizer).createProject(projectName, refundRate, penalties);
        const now = await ethers.provider.getBlock("latest").then(b => b.timestamp);
        await auction.connect(organizer).createAuction(0, auctionName, 3600, now + 14400, slots);
    }

    it("Should create auction with resource limit", async function () {
        await registry.connect(organizer).createProject("Mathematics", 9000, [0, 2000, 3000, 5000]);

        const now = await ethers.provider.getBlock("latest").then(b => b.timestamp);
        // Аукцион: 2 места, торги 1 час, урок через 2 часа
        await auction.connect(organizer).createAuction(0, "Lab #1", 3600, now + 7200, 2);

        const auc = await auction.auctions(0);
        expect(auc.resourceLimit).to.equal(2);
        expect(auc.active).to.equal(true);
    });

    it("Should allow bidding and calculate leaderboard position", async function () {
        // 1. Setup: Проект + Аукцион
        await setupProjectAndAuction();

        // 2. Подготовка: минтим токены троим студентам
        for (const s of [student1, student2, student3]) {
            await token.mint(s.address, 0, 500, "0x");
            await token.connect(s).setApprovalForAll(await auction.getAddress(), true);
        }

        // 3. Ставки: 100, 200, 150
        await auction.connect(student1).placeBid(0, 100);
        await auction.connect(student2).placeBid(0, 200);
        await auction.connect(student3).placeBid(0, 150);

        // 4. Проверка лидерборда
        const [users, bids] = await auction.getLeaderboard(0, 10);
        expect(users.length).to.equal(3);

        // Проверка: student2 (200) должен быть в топ-2 (гарантированные места)
        const inTop = await auction.isStudentInGuaranteedTop(0, student2.address);
        expect(inTop).to.equal(true);

        // student1 (100) - НЕ в топ-2
        const notInTop = await auction.isStudentInGuaranteedTop(0, student1.address);
        expect(notInTop).to.equal(false);
    });

    it("Should apply penalty on cancel after auction ends", async function () {
        // Полный изолированный сетап
        await setupProjectAndAuction();

        await token.mint(student2.address, 0, 500, "0x");
        await token.connect(student2).setApprovalForAll(await auction.getAddress(), true);

        await auction.connect(student2).placeBid(0, 200); 
        expect(await token.balanceOf(student2.address, 0)).to.equal(300n); // 500 - 200

        // Мотаем время: торги закончились (прошло > 3600 сек)
        await ethers.provider.send("evm_increaseTime", [3660]);
        await ethers.provider.send("evm_mine");

        await auction.connect(student2).cancelBid(0);

        // Проверка: 300 (остаток) + 160 (возврат 200 - 20% штраф) = 460
        expect(await token.balanceOf(student2.address, 0)).to.equal(460n);
    });

    it("Should allow free cancel for non-guaranteed student", async function () {
        // student1 НЕ в гарантированном месте, отменяется после окончания торгов
        // Штраф = 0%

        await setupProjectAndAuction();

        // Студент с маленькой ставкой (не попадает в гарантированные места)
        await token.mint(student1.address, 0, 500, "0x");
        await token.connect(student1).setApprovalForAll(await auction.getAddress(), true);
        await auction.connect(student1).placeBid(0, 100);

        // Добавляем ДВУХ студентов с БОЛЬШИМИ ставками, чтобы вытеснить student1 из топа
        for (const s of [student2, student3]) {
            await token.mint(s.address, 0, 500, "0x");
            await token.connect(s).setApprovalForAll(await auction.getAddress(), true);
            await auction.connect(s).placeBid(0, 200); // ← больше, чем у student1
        }

        const initialBalance = await token.balanceOf(student1.address, 0); // 400
        expect(initialBalance).to.equal(400n); 

        // Мотаем время: торги закончились
        await ethers.provider.send("evm_increaseTime", [3660]);
        await ethers.provider.send("evm_mine");

        // Теперь student1 НЕ в гарантированном топе → штраф 0%
        await auction.connect(student1).cancelBid(0);

        // Штраф 0%, вернулось 100: 400 + 100 = 500
        expect(await token.balanceOf(student1.address, 0)).to.equal(500n);
    });

    it("Should process attendance refund by teacher", async function () {
        // student3 пришёл на занятие, учитель подтверждает
        await setupProjectAndAuction();

        await token.mint(student3.address, 0, 500, "0x");
        await token.connect(student3).setApprovalForAll(await auction.getAddress(), true);
        await auction.connect(student3).placeBid(0, 150);

        const initialBalance = await token.balanceOf(student3.address, 0); // 350

        //refundRate = 9000 (90%), возврат: 150 * 0.9 = 135
        await auction.connect(organizer).processAttendanceRefund(0, student3.address);

        expect(await token.balanceOf(student3.address, 0)).to.equal(initialBalance + 135n); // 470
    });

    it("Should close day: refund non-absent, penalize absent", async function () {
        // Создаём проект с правильными настройками:
        // - refundRate = 9000 (90% возврата для присутствующих)
        // - penalties = [0, 2000, 3000, 9000] в базисных пунктах (0%, 20%, 30%, 90%)
        await registry.connect(organizer).createProject("Physics", 9000, [0, 2000, 3000, 9000]);

        const now = await ethers.provider.getBlock("latest").then(b => b.timestamp);
        await auction.connect(organizer).createAuction(0, "Lab Physics", 3600, now + 14400, 3);

        // === Студент А (прогульщик) ===
        await token.mint(student1.address, 0, 500, "0x");
        await token.connect(student1).setApprovalForAll(await auction.getAddress(), true);
        await auction.connect(student1).placeBid(0, 100); // Ставка 100 токенов

        // === Студент Б (присутствует) ===
        await token.mint(student2.address, 0, 500, "0x");
        await token.connect(student2).setApprovalForAll(await auction.getAddress(), true);
        await auction.connect(student2).placeBid(0, 100);

        // Учитель помечает student1 как absent
        await auction.connect(organizer).markAsAbsent(0, student1.address);

        // Мотаем время: урок начался
        await ethers.provider.send("evm_increaseTime", [14400]); 
        await ethers.provider.send("evm_mine");

        // Фиксируем балансы ДО закрытия дня
        // У каждого: 500 - 100 (ставка) = 400
        const balAbsentBefore = await token.balanceOf(student1.address, 0); // 400
        const balNormalBefore = await token.balanceOf(student2.address, 0); // 400

        // Закрытие дня: возвраты и штрафы
        await auction.connect(organizer).closeDayAndRefundRemaining(0);

        // === РАСЧЁТЫ ===
        // student1 (absent): 
        // - penalty = penalties[3] = 9000 (90% в basis points)
        // - Штраф: 100 * 9000 / 10000 = 90 токенов
        // - Возврат: 100 - 90 = 10 токенов
        // - Итог: 400 + 10 = 410
        expect(await token.balanceOf(student1.address, 0)).to.equal(410n);

        // student2 (не absent и не отмечен (т.е. не успел сдать)):
        // - Возврат: 100%
        // - Итог: 400 + 100 = 500
        expect(await token.balanceOf(student2.address, 0)).to.equal(500n);
    });

    it("Should prevent cancel after lesson started", async function () {
        await setupProjectAndAuction(); // ✅ Создаём проект + аукцион
    
        await token.mint(student3.address, 0, 500, "0x");
        await token.connect(student3).setApprovalForAll(await auction.getAddress(), true);
        await auction.connect(student3).placeBid(0, 100);

        // Мотаем время: урок уже начался (> 4 часа от создания)
        await ethers.provider.send("evm_increaseTime", [14400]);
        await ethers.provider.send("evm_mine");

        await expect(
            auction.connect(student3).cancelBid(0)
        ).to.be.revertedWith("Lesson already started, use code confirmation");
    });
});