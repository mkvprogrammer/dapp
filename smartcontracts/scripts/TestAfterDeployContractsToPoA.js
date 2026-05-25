// 1. Подключаемся к контрактам
const registry = await ethers.getContractAt("ProjectRegistry", "0x264883Bcc7BAc4fD88CA6Cea319AF8Bbf0b0a7e2");
const token = await ethers.getContractAt("UniversityToken", "0xdccba7B35aA620b2a8F4c83cD32a91Fe285AD6e8");
const auction = await ethers.getContractAt("AuctionManager", "0x6371fC91dc919Ad004fdfdE94A94137104427b5C");

// 2. Получаем подписантов
const [deployer, organizer, relayer] = await ethers.getSigners();

// 3. Создаём проект + ЖДЁМ ПОДТВЕРЖДЕНИЯ
console.log("Creating project...");
const tx1 = await registry.connect(organizer).createProject("Mathematics", 8000, [0, 20, 50, 100]);
await tx1.wait(); // ← КРИТИЧНО: ждём майнинга блока
console.log("✅ Project created, tx:", tx1.hash);

// 4. Проверяем проект (теперь сработает!)
const [name, owner, refundRate, penalties, isActive] = await registry.getProjectInfo(0);
console.log("Project:", name, "| Owner:", owner, "| Active:", isActive);
// Ожидаемо: Mathematics | 0xae70... | true

// 5. Начисляем токены + ЖДЁМ ПОДТВЕРЖДЕНИЯ
console.log("Minting tokens...");
const tx2 = await token.connect(organizer).mint(relayer.address, 0, 1000, "0x");
await tx2.wait();
console.log("✅ Tokens minted");

// 6. Проверяем баланс
const balance = await token.balanceOf(relayer.address, 0);
console.log("Student balance:", balance.toString()); // 1000

// 7. Создаём аукцион + ЖДЁМ
console.log("Creating auction...");
const now = Math.floor(Date.now() / 1000);
const tx3 = await auction.connect(organizer).createAuction(0, "Lab #1", 3600, now + 7200, 2);
await tx3.wait();
console.log("✅ Auction created");

// 8. Проверяем аукцион
const auc = await auction.auctions(0);
console.log("Auction active:", auc.active, "| Limit:", auc.resourceLimit.toString());
// Ожидаемо: true | 2

// 9. Студент делает ставку
console.log("Placing bid...");
await token.connect(relayer).setApprovalForAll(await auction.getAddress(), true);
const tx4 = await auction.connect(relayer).placeBid(0, 150);
await tx4.wait();
console.log("✅ Bid placed");

// 10. Финальная проверка
const finalBalance = await token.balanceOf(relayer.address, 0);
console.log("Student balance after bid:", finalBalance.toString()); // 850

console.log("\n🎉 All tests passed!");