/**
 * Офлайн-компиляция Solidity через npm-пакет solc (без binaries.soliditylang.org).
 * Генерирует артефакты в формате Hardhat для deploy.js и backend.
 */
const fs = require("fs");
const path = require("path");
const solc = require("solc");

const ROOT = path.join(__dirname, "..");
const CONTRACTS_DIR = path.join(ROOT, "contracts");
const ARTIFACTS_DIR = path.join(ROOT, "artifacts", "contracts");
const NODE_MODULES = path.join(ROOT, "node_modules");

const SETTINGS = {
  optimizer: { enabled: true, runs: 200 },
  evmVersion: "paris",
  outputSelection: {
    "*": {
      "*": ["abi", "evm.bytecode", "evm.deployedBytecode"],
    },
  },
};

function findImports(importPath) {
  const candidates = [];

  if (importPath.startsWith("@openzeppelin/")) {
    candidates.push(path.join(NODE_MODULES, importPath));
  } else if (importPath.startsWith("./") || importPath.startsWith("../")) {
    candidates.push(path.join(CONTRACTS_DIR, importPath));
    candidates.push(path.join(CONTRACTS_DIR, importPath.replace(/^\.\//, "")));
  } else {
    candidates.push(path.join(CONTRACTS_DIR, importPath));
    candidates.push(path.join(NODE_MODULES, importPath));
  }

  for (const filePath of candidates) {
    if (fs.existsSync(filePath)) {
      return { contents: fs.readFileSync(filePath, "utf8") };
    }
  }

  return { error: `File not found: ${importPath}` };
}

function buildSources() {
  const sources = {};
  for (const file of fs.readdirSync(CONTRACTS_DIR)) {
    if (!file.endsWith(".sol")) continue;
    const sourceName = `contracts/${file}`;
    sources[sourceName] = {
      content: fs.readFileSync(path.join(CONTRACTS_DIR, file), "utf8"),
    };
  }
  return sources;
}

function writeArtifacts(output) {
  if (output.errors?.some((e) => e.severity === "error")) {
    console.error(output.errors);
    throw new Error("Solc compilation failed");
  }

  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });

  for (const [sourceName, contracts] of Object.entries(output.contracts || {})) {
    const base = path.basename(sourceName);
    const outDir = path.join(ARTIFACTS_DIR, base);

    for (const [contractName, data] of Object.entries(contracts)) {
      fs.mkdirSync(outDir, { recursive: true });
      const artifact = {
        _format: "hh-sol-artifact-1",
        contractName,
        sourceName,
        abi: data.abi,
        bytecode: `0x${data.evm.bytecode.object}`,
        deployedBytecode: `0x${data.evm.deployedBytecode.object}`,
        linkReferences: data.evm.bytecode.linkReferences || {},
        deployedLinkReferences: data.evm.deployedBytecode.linkReferences || {},
      };
      fs.writeFileSync(
        path.join(outDir, `${contractName}.json`),
        JSON.stringify(artifact, null, 2),
      );
      console.log(`  ✓ ${sourceName}:${contractName}`);
    }
  }
}

function main() {
  console.log("==> Offline compile (solc npm)...");
  const input = {
    language: "Solidity",
    sources: buildSources(),
    settings: SETTINGS,
  };

  const compiled = solc.compile(JSON.stringify(input), { import: findImports });
  const output = JSON.parse(compiled);
  writeArtifacts(output);
  console.log("==> Artifacts written to artifacts/contracts/");
}

main();
