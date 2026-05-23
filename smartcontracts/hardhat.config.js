require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config(); // <-- Добавлено

module.exports = {
  solidity: "0.8.28",
  networks: {
    localPoA: {
      url: "http://127.0.0.1:8541",
      chainId: 1337,
      gas: 0,
      gasPrice: 0,
      accounts: [
        process.env.PRIVATE_KEY_VALIDATOR, // <-- Читаем из .env
        process.env.PRIVATE_KEY_RELAYER    // <-- Читаем из .env
      ]
    }
  }
};

// require("@nomicfoundation/hardhat-toolbox");

// /** @type import('hardhat/config').HardhatUserConfig */
// module.exports = {
//   solidity: "0.8.28",
// };
