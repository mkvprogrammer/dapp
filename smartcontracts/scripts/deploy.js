// Деплоит контракты в блокчейн
const hre = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer, organizer, relayer] = await hre.ethers.getSigners();

  console.log("🚀 Deploying with account:", deployer.address);
  console.log("Organizer:", organizer.address);
  console.log("Relayer:", relayer.address);

  // 1. Деплоим ProjectRegistry (не требует аргументов)
  const Registry = await hre.ethers.getContractFactory("ProjectRegistry");
  const registry = await Registry.deploy();
  await registry.waitForDeployment();
  console.log("✅ ProjectRegistry deployed:", await registry.getAddress());

  // 2. Деплоим UniversityToken, передавая адрес реестра в конструктор
  const Token = await hre.ethers.getContractFactory("UniversityToken");
  const token = await Token.deploy(await registry.getAddress()); // <--- ПЕРЕДАЕМ АДРЕС
  await token.waitForDeployment();
  console.log("✅ UniversityToken deployed:", await token.getAddress());

  // 3. AuctionManager
  const Auction = await hre.ethers.getContractFactory("AuctionManager");
  const auction = await Auction.deploy(
    await token.getAddress(),
    await registry.getAddress()
  );
  await auction.waitForDeployment();
  console.log("✅ AuctionManager deployed:", await auction.getAddress());

  // === НАСТРОЙКА РОЛЕЙ ===
  
  // Дать аукциону право сжигать токены (для штрафов)
  const ADMIN_ROLE = await token.DEFAULT_ADMIN_ROLE();
  await token.grantRole(ADMIN_ROLE, await auction.getAddress());
  console.log("🔑 Granted ADMIN_ROLE on Token to AuctionManager");

  // Выдать ORGANIZER_ROLE преподавателю
  const ORG_ROLE = await registry.ORGANIZER_ROLE();
  await registry.grantRole(ORG_ROLE, organizer.address);
  await auction.grantRole(ORG_ROLE, organizer.address);
  // В UniversityToken роль ORGANIZER_ROLE уже определена, 
  // но выдавать её организатору нужно, если он будет вызывать mint() напрямую.
  // В нашей архитектуре mint вызывает бэкенд от имени организатора, 
  // так что выдадим роль и там для полноты картины.
  await token.grantRole(ORG_ROLE, organizer.address);
  console.log(`🔑 Granted ORGANIZER_ROLE to ${organizer.address}`);

  // (Опционально) Выдать USER_ROLE, если студенты должны создавать аукционы
  const USER_ROLE = await auction.USER_ROLE();
  await auction.grantRole(USER_ROLE, relayer.address);
  console.log(`🔑 Granted USER_ROLE to ${relayer.address}`);

  // === СОХРАНЕНИЕ АДРЕСОВ В ФАЙЛ ===
  const config = {
    network: "localPoA",
    chainId: 1337,
    contracts: {
      UniversityToken: await token.getAddress(),
      ProjectRegistry: await registry.getAddress(),
      AuctionManager: await auction.getAddress()
    },
    roles: {
      admin: deployer.address,
      organizer: organizer.address,
      relayer: relayer.address
    }
  };

  fs.writeFileSync(
    "./deployed.json",
    JSON.stringify(config, null, 2)
  );
  console.log("\n📄 Addresses saved to deployed.json");

  console.log("\n🎉 Deployment complete! Ready for Phase 3 (Backend).");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});