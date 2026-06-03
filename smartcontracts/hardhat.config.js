require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

// Заглушки только для `hardhat compile` в Docker build (без .env)
const PLACEHOLDER_KEY =
  "0xac0974bec39a17e36ba4a6b4d0bf260c9c2108a36c117e393adbd9e91e470000";

function poaAccounts() {
  const keys = [
    process.env.LOCAL_POA_DEPLOYER_KEY,
    process.env.LOCAL_POA_ORGANIZER_KEY,
    process.env.LOCAL_POA_RELAYER_KEY,
  ].filter(Boolean);
  if (keys.length === 3) return keys;
  return [PLACEHOLDER_KEY, PLACEHOLDER_KEY, PLACEHOLDER_KEY];
}

const poaNetwork = {
  chainId: 1337,
  gas: 0,
  gasPrice: 0,
  accounts: poaAccounts(),
};

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      evmVersion: "paris",
    },
  },
  networks: {
    localPoA: {
      url: process.env.BLOCKCHAIN_RPC_URL || "http://127.0.0.1:8541",
      ...poaNetwork,
    },
    dockerPoA: {
      url: process.env.BLOCKCHAIN_RPC_URL || "http://node1:8545",
      ...poaNetwork,
    },
  },
};



// require("@nomicfoundation/hardhat-toolbox");
// require("dotenv").config(); // <-- Добавлено

// module.exports = {
//   solidity: "0.8.28",
//   networks: {
//     localPoA: {
//       url: "http://127.0.0.1:8541",
//       chainId: 1337,
//       gas: 0,
//       gasPrice: 0,
//       accounts: [
//         process.env.PRIVATE_KEY_VALIDATOR, // <-- Читаем из .env
//         process.env.PRIVATE_KEY_RELAYER    // <-- Читаем из .env
//       ]
//     }
//   }
// };

// require("@nomicfoundation/hardhat-toolbox");

// /** @type import('hardhat/config').HardhatUserConfig */
// module.exports = {
//   solidity: "0.8.28",
// };
