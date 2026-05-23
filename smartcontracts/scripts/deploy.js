// Деплоит контракт в блокчейн
const hre = require("hardhat");

async function main() {
  // Замените "MyContract" на имя вашего контракта
  const MyContract = await hre.ethers.getContractFactory("MyContract");
  
  console.log("Deploying contract...");
  
  const myContract = await MyContract.deploy();
  
  await myContract.waitForDeployment();
  
  console.log(`Contract deployed to: ${await myContract.getAddress()}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});