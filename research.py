from constants import TEST_SPEEDUP
import objects

class Research(object):
    buildTime = 0
    level = 0
    dependencies = 1
    units = []  # units that can be created after this research is done
    uid = 0

    @classmethod
    def on_start(cls, player):
        #get's called when research starts
        pass

    @classmethod
    def on_cancel(cls,player):
        #called when the research is cancelled for whatever reason
        pass

    @classmethod
    def on_completion(cls, player):
        # interface-ish method
        pass
        # c = objects.Objects.get_controller()
        # doesn't work because units are 
        # for obj in c.selectedUnits:
        #     obj.clear_action_menu(c.map, c.cm, c.player)
        #     obj.display_action_menu(c.map, c.cm, c.player)
        

class PortScanner(Research):
    buildTime = 20 / TEST_SPEEDUP
    level = 1
    uid = 2

    @classmethod
    def on_start(cls, player):
        player.unitActionLists["SoftwareUpdater"].remove("RPortScanner")

    @classmethod
    def on_cancel(cls,player):
        player.unitActionLists["SoftwareUpdater"].append("RPortScanner")

    @classmethod
    def on_completion(cls, player):
        Research.on_completion(player)
        player.unitActionLists["Installer"].append("BFirewall")
        player.unitActionLists["Server"].append("TPing")
        player.unitActionLists["SoftwareUpdater"].append("RPingResearch")


class PingResearch(Research):
    buildTime = 20 / TEST_SPEEDUP
    level = 1
    uid = 3

    @classmethod
    def on_start(cls, player):
        player.unitActionLists["SoftwareUpdater"].remove("RPingResearch")

    @classmethod
    def on_cancel(cls,player):
        player.unitActionLists["SoftwareUpdater"].append("RPingResearch")

    @classmethod
    def on_completion(cls, player):
        Research.on_completion(player)
        player.unitActionLists["Ping"].append("UPingOfDeath")
        player.unitActionLists["AlgorithmFactory"].append("TBufferOverflow")
        player.unitActionLists["SoftwareUpdater"].append("RNetworkTopology")
        player.unitActionLists["SoftwareUpdater"].append("RFPGA")

class FPGA(Research):
    buildTime = 25 / TEST_SPEEDUP
    level = 1

    @classmethod
    def on_start(cls, player):
        player.unitActionLists["SoftwareUpdater"].remove("RFPGA")

    @classmethod
    def on_cancel(cls,player):
        player.unitActionLists["SoftwareUpdater"].append("RFPGA")

    @classmethod
    def on_completion(cls, player):
        Research.on_completion(player)
        player.unitActionLists["APTGet"].append("BCPU")
        player.unitActionLists["Server"].append("TAPTGet")
        player.unitActionLists["SoftwareUpdater"].append("RAdvancedAlgorithms")


class BigData(Research):
    buildTime = 25 / TEST_SPEEDUP
    level = 1

    @classmethod
    def on_start(cls, player):
        player.unitActionLists["SoftwareUpdater"].remove("RBigData")

    @classmethod
    def on_cancel(cls,player):
        player.unitActionLists["SoftwareUpdater"].append("RBigData")

    @classmethod
    def on_completion(cls, player):
        Research.on_completion(player)
        player.unitActionLists["APTGet"].append("BDatabase")
        player.unitActionLists["AlgorithmFactory"].append("TSQLInjection")
        player.unitActionLists["SoftwareUpdater"].append("RHandshake")
        player.unitActionLists["SoftwareUpdater"].append("RRSA")
        

class ParallelDistributed(Research):
    buildTime = 20 / TEST_SPEEDUP
    level = 2
    dependencies = 6
    uid = 7

    @classmethod
    def on_start(cls, player):
        pass

    @classmethod
    def on_cancel(cls,player):
        pass


class Handshake(Research):
    buildTime = 20 / TEST_SPEEDUP
    level = 2
    dependencies = 6
    uid = 11

    @classmethod
    def on_start(cls, player):
        player.unitActionLists["SoftwareUpdater"].remove("RHandshake")

    @classmethod
    def on_cancel(cls,player):
        player.unitActionLists["SoftwareUpdater"].append("RHandshake")

    @classmethod
    def on_completion(cls, player):
        Research.on_completion(player)
        player.unitActionLists["AlgorithmFactory"].append("THandshake")


class AdvancedAlgorithm(Research):
    buildTime = 30 / TEST_SPEEDUP
    level = 3
    dependencies = 385
    uid = 13

    @classmethod
    def on_start(cls, player):
        player.unitActionLists["SoftwareUpdater"].remove("RAdvancedAlgorithms")

    @classmethod
    def on_cancel(cls,player):
        player.unitActionLists["SoftwareUpdater"].append("RAdvancedAlgorithms")

    @classmethod
    def on_completion(cls, player):
        Research.on_completion(player)
        player.unitActionLists["AlgorithmFactory"].append("TDNSPoison")
        player.unitActionLists["AlgorithmFactory"].append("TSpoof")

class NetworkTopology(Research):
    buildTime = 30 / TEST_SPEEDUP
    level = 3
    dependencies = 385
    uid = 17
    
    @classmethod
    def on_start(cls, player):
        player.unitActionLists["SoftwareUpdater"].remove("RNetworkTopology")

    @classmethod
    def on_cancel(cls,player):
        player.unitActionLists["SoftwareUpdater"].append("RNetworkTopology")

    @classmethod
    def on_completion(cls, player):
        Research.on_completion(player)
        player.unitActionLists["SoftwareUpdater"].append("RBigData")
        player.unitActionLists["Firewall"].append("USinkhole")



class RSA(Research):
    buildTime = 20 / TEST_SPEEDUP
    level = 3
    dependencies = 385
    uid = 19

    @classmethod
    def on_start(cls, player):
        player.unitActionLists["SoftwareUpdater"].remove("RRSA")

    @classmethod
    def on_cancel(cls,player):
        player.unitActionLists["SoftwareUpdater"].append("RRSA")

    @classmethod
    def on_completion(cls, player):
        Research.on_completion(player)
        player.unitActionLists["APTGet"].append("BRSA")


class EMP(Research):
    buildTime = 40 / TEST_SPEEDUP
    level = 4
    dependencies = 4199
    uid = 23

    @classmethod
    def on_start(cls, player):
        pass

    @classmethod
    def on_cancel(cls,player):
        pass


'''RESEARCH_OPTIONS'''

RESEARCH = {
    "RPortScanner": PortScanner, "RPingResearch": PingResearch,  # level 1
    "RFPGA": FPGA, "RPandD": ParallelDistributed, "RBigData" : BigData, "RHandshake": Handshake,  # level 2
    "RAdvancedAlgorithms": AdvancedAlgorithm, "RNetworkTopology": NetworkTopology, "RRSA": RSA,  # level 3
    "REMP": EMP  # level 4
}
