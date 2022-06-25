from dataclasses import dataclass, asdict, fields, field, InitVar
import time
import requests

class What_Do_To_State(Enum):
    bank = 2
    only_buy = 0
    only_sell = 1

@dataclass
class Base_Currency(Get_Dict_base):
    keys: int
    metal: float

@dataclass
class Price_List_Item(Get_Dict_base):
    sku: str
    name: str
    enabled: bool
    autoprice: bool
    min: int
    max: int
    intent: What_Do_To_State
    buy: Base_Currency
    sell: Base_Currency
    time: int
    group: str
    isPartialPriced: bool
    minMargin: int
    maxBuyPrice: Base_Currency

@dataclass
class Pricelist_Class(Get_Dict_base):
    autobot_url: str
    items: Dict[str, Price_List_Item] = field(default_factory=list)

    last_loaded: float = 0.0
    times_loaded: int = 0
    
    def __post_init__(self):
        res = requests.get(self.autobot_url + "/pricelist")
        if res.status_code != 200:
            print(res.status_code)
            print(res.text)
            raise

        data = res.json()
        self.items = {sku:Price_List_Item(
            sku,
            data[sku]["name"],
            data[sku]["enabled"],
            data[sku]["autoprice"],
            data[sku]["min"],
            data[sku]["max"],
            What_Do_To_State(data[sku]["intent"]),
            Base_Currency(
                data[sku]["buy"]["keys"],
                data[sku]["buy"]["metal"]
            ),
            Base_Currency(
                data[sku]["sell"]["keys"],
                data[sku]["sell"]["metal"]
            ),
            data[sku]["time"],
            data[sku]["group"],
            data[sku]["isPartialPriced"],
            data[sku]["minMargin"],
            Base_Currency(
                data[sku]["maxBuyPrice"]["keys"],
                data[sku]["maxBuyPrice"]["metal"]
            )
        ) for sku in data}

        self.last_loaded = time.time()
        self.times_loaded += 1

    def get_param_string(self, param_dict):
        return_str = ""
        for key in param_dict: return_str += f"{key}={param_dict[key]}" if return_str == "" else f"&{key}={param_dict[key]}"
        
        return return_str

    def add(self, param_dict, reload_pricelist=True):
        requests.post(f"{self.autobot_url}" + "/add", data={
            "message": self.get_param_string(param_dict)
        })

        if reload_pricelist:
            self.__post_init__()

    def update(self, param_dict, reload_pricelist=True):
        requests.post(f"{self.autobot_url}" + "/update", data={
            "message": self.get_param_string(param_dict)
        })

        if reload_pricelist:
            self.__post_init__()

    def remove(self, sku, reload_pricelist=True):
        requests.post(f"{self.autobot_url}" + "/remove", data={
            "message": f"sku={sku}"
        })

        if reload_pricelist:
            self.__post_init__()

    def wipe(self):
        print("Wiping pricelist")

        requests.post(f"{self.autobot_url}" + "/remove", data={
            "message": f"all=true&i_am_sure=yes_i_am"
        })

        print("Done clearing the pricelist.")
        self.__post_init__()

    def check_bad_item(self, sku):
        if sku in self.items:
            self.remove(sku)
            print(f"Sku {sku} was bad checked, found in the pricelist and removed")

        else:

            print(f"Sku {sku} was bad checked but not found")

    def check_item(self, param_dict):
        if not "sku" in param_dict: raise

        if param_dict["sku"] in self.items:
            print(f"Sku {param_dict['sku']} was good checked but was already in the pricelist, updating it ")
            self.update(param_dict)

        else:
            print(f"Sku {param_dict['sku']} was good checkedand not in the pricelist, adding it ")
            self.add(param_dict) 

