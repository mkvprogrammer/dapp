require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.28", // Убедитесь, что эта версия совпадает с pragma в ваших контрактах
  networks: {
    localPoA: {
      url: "http://127.0.0.1:8541",
      chainId: 1337,
      gas: 0,       // Или уберите эту строку, если нода требует авто-расчет
      gasPrice: 0,  // Или уберите эту строку
      accounts: [
        "0xВАШ_ПРИВАТНЫЙ_КЛЮЧ_ВАЛИДАТОРА", 
        "0xВАШ_ПРИВАТНЫЙ_КЛЮЧ_РЕЛЕЙЕРА"    
      ]
    }
  }
};


// require("@nomicfoundation/hardhat-toolbox");

// /** @type import('hardhat/config').HardhatUserConfig */
// module.exports = {
//   solidity: "0.8.28",
// };
