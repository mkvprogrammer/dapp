require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  // Переделываем solidity из строки в объект с расширенными настройками
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      },
      evmVersion: "paris"
    }
  },
  networks: {
    localPoA: {
      url: "http://127.0.0.1:8541",
      chainId: 1337,
      gas: 0,
      gasPrice: 0,
      accounts: [
        process.env.LOCAL_POA_DEPLOYER_KEY,
        process.env.LOCAL_POA_ORGANIZER_KEY,
        process.env.LOCAL_POA_RELAYER_KEY
      ]
    }
  }
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
