const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("LGCSEToken", function () {
  let LGCSEToken;
  let lgcseToken;
  let owner;
  let addr1;
  let addr2;
  let addrs;

  beforeEach(async function () {
    LGCSEToken = await ethers.getContractFactory("LGCSEToken");
    [owner, addr1, addr2, ...addrs] = await ethers.getSigners();
    lgcseToken = await LGCSEToken.deploy();
    await lgcseToken.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await lgcseToken.owner()).to.equal(owner.address);
    });

    it("Should assign initial supply to owner", async function () {
      const ownerBalance = await lgcseToken.balanceOf(owner.address);
      expect(await lgcseToken.totalSupply()).to.equal(ownerBalance);
    });

    it("Should have correct token price", async function () {
      expect(await lgcseToken.TOKEN_PRICE()).to.equal(ethers.parseEther("0.01"));
    });
  });

  describe("Token Purchase", function () {
    it("Should allow users to buy tokens", async function () {
      const buyAmount = ethers.parseEther("1"); // 1 ETH
      const expectedTokens = buyAmount / ethers.parseEther("0.01");
      
      await expect(lgcseToken.connect(addr1).buyTokens({ value: buyAmount }))
        .to.emit(lgcseToken, "TokensPurchased")
        .withArgs(addr1.address, expectedTokens, buyAmount);
      
      const balance = await lgcseToken.balanceOf(addr1.address);
      expect(balance).to.equal(expectedTokens);
    });

    it("Should fail if no ETH sent", async function () {
      await expect(lgcseToken.connect(addr1).buyTokens({ value: 0 }))
        .to.be.revertedWith("Invalid amount");
    });
  });

  describe("Project Creation", function () {
    it("Should allow user to create project", async function () {
      const projectName = "Test Project";
      const description = "Test Description";
      const fundingGoal = 1000;
      const duration = 7;

      await expect(lgcseToken.connect(addr1).createProject(projectName, description, fundingGoal, duration))
        .to.emit(lgcseToken, "ProjectCreated")
        .withArgs(0, projectName, addr1.address);

      const project = await lgcseToken.projects(0);
      expect(project.name).to.equal(projectName);
      expect(project.creator).to.equal(addr1.address);
      expect(project.fundingGoal).to.equal(fundingGoal * 10**18);
    });
  });

  describe("Staking", function () {
    it("Should allow users to stake tokens", async function () {
      // First buy some tokens
      await lgcseToken.connect(addr1).buyTokens({ value: ethers.parseEther("1") });
      
      const stakeAmount = ethers.parseEther("50");
      const lockDays = 30;
      
      await lgcseToken.connect(addr1).approve(await lgcseToken.getAddress(), stakeAmount);
      
      await expect(lgcseToken.connect(addr1).stake(stakeAmount, lockDays))
        .to.emit(lgcseToken, "Staked")
        .withArgs(addr1.address, stakeAmount, anyValue);
      
      const stakeInfo = await lgcseToken.getStakeInfo(addr1.address);
      expect(stakeInfo.amount).to.equal(stakeAmount);
    });
  });
});
