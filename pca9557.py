"""
PCA9557 I2C I/O扩展芯片驱动库
适用于MicroPython

PCA9557是一个8位I/O扩展芯片，通过I2C接口控制
- 8个可配置为输入或输出的引脚
- 支持极性反转
- 工作电压2.3V-5.5V

作者: Cascade
日期: 2025-05-08
"""

import sys

# PCA9557 I2C地址和寄存器定义
PCA9557_ADDR = 0x19  # 默认I2C地址: 0x19 (可根据实际电路修改)
PCA9557_INPUT_REG = 0x00  # 输入端口寄存器 (只读)
PCA9557_OUTPUT_REG = 0x01  # 输出端口寄存器 (读/写)
PCA9557_POLARITY_REG = 0x02  # 极性反转寄存器 (读/写)
PCA9557_CONFIG_REG = 0x03  # 配置寄存器 (读/写) - 0:输出, 1:输入

# 引脚状态和模式定义
PIN_LOW = 0
PIN_HIGH = 1
PIN_OUTPUT = 0
PIN_INPUT = 1
PIN_NON_INVERTED = 0
PIN_INVERTED = 1

class PCA9557:
    """PCA9557 I2C I/O扩展芯片控制类
    
    提供对PCA9557的完整控制，包括:
    - 引脚输入/输出模式配置
    - 输出引脚的值控制
    - 输入引脚的值读取
    - 引脚极性控制
    
    默认配置: 所有引脚设为输出模式，输出高电平
    """
    def __init__(self, i2c, addr=PCA9557_ADDR, debug=False):
        """初始化PCA9557
        
        Args:
            i2c: machine.I2C对象
            addr: PCA9557的I2C地址，默认0x19
            debug: 是否启用调试输出
        """
        self.i2c = i2c
        self.addr = addr
        self.debug = debug
        
        # 读取当前配置和输出状态
        try:
            # 读取当前配置
            config = self._read_reg(PCA9557_CONFIG_REG)
            output = self._read_reg(PCA9557_OUTPUT_REG)
            if self.debug:
                print(f"PCA9557初始状态 - 配置: 0x{config:02X}, 输出: 0x{output:02X}")
            
            # 初始化: 设置所有引脚为输出模式
            self._write_reg(PCA9557_CONFIG_REG, 0x00)
            if self.debug:
                print("PCA9557已配置为全输出模式")
            
            # 设置所有引脚为高电平
            self._write_reg(PCA9557_OUTPUT_REG, 0xFF)
            if self.debug:
                print("PCA9557输出设置为全高电平")
            
            # 验证写入是否成功
            if self.debug:
                config = self._read_reg(PCA9557_CONFIG_REG)
                output = self._read_reg(PCA9557_OUTPUT_REG)
                print(f"PCA9557验证 - 配置: 0x{config:02X}, 输出: 0x{output:02X}")
            
        except Exception as e:
            print(f"PCA9557初始化失败: {e}")
            if self.debug:
                sys.print_exception(e)
            raise
    
    def _write_reg(self, reg, value):
        """写PCA9557寄存器
        
        Args:
            reg: 寄存器地址
            value: 要写入的值
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            self.i2c.writeto_mem(self.addr, reg, bytes([value]))
            return True
        except Exception as e:
            if self.debug:
                print(f"写寄存器0x{reg:02X}失败: {e}")
            return False
    
    def _read_reg(self, reg):
        """读PCA9557寄存器
        
        Args:
            reg: 寄存器地址
            
        Returns:
            int: 寄存器值，失败返回0
        """
        try:
            data = self.i2c.readfrom_mem(self.addr, reg, 1)
            return data[0]
        except Exception as e:
            if self.debug:
                print(f"读寄存器0x{reg:02X}失败: {e}")
            return 0
            
    def _format_binary(self, value):
        """格式化为8位二进制字符串
        
        Args:
            value: 整数值
            
        Returns:
            string: 8位二进制字符串，例如"00101101"
        """
        # 使用格式化字符串而不是bin()和zfill()方法
        binary = ""
        for i in range(7, -1, -1):
            if value & (1 << i):
                binary += "1"
            else:
                binary += "0"
        return binary
    
    def set_pin_mode(self, pin, mode):
        """设置引脚模式 (输入/输出)
        
        Args:
            pin: 引脚号 (0-7)
            mode: PIN_OUTPUT(0) 或 PIN_INPUT(1)
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        if not 0 <= pin <= 7:
            if self.debug:
                print(f"引脚号无效: {pin}")
            return False
            
        current = self._read_reg(PCA9557_CONFIG_REG)
        if mode == PIN_OUTPUT:
            # 配置为输出模式 (对应位清0)
            new_value = current & ~(1 << pin)
        else:
            # 配置为输入模式 (对应位置1)
            new_value = current | (1 << pin)
        
        return self._write_reg(PCA9557_CONFIG_REG, new_value)
    
    def set_pin_value(self, pin, value):
        """设置输出引脚的电平值
        
        Args:
            pin: 引脚号 (0-7)
            value: PIN_LOW(0) 或 PIN_HIGH(1)
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        if not 0 <= pin <= 7:
            if self.debug:
                print(f"引脚号无效: {pin}")
            return False
            
        current = self._read_reg(PCA9557_OUTPUT_REG)
        if value == PIN_LOW:
            # 设置为低电平 (对应位清0)
            new_value = current & ~(1 << pin)
        else:
            # 设置为高电平 (对应位置1)
            new_value = current | (1 << pin)
        
        result = self._write_reg(PCA9557_OUTPUT_REG, new_value)
        if result and self.debug:
            print(f"引脚{pin}设为{'高' if value else '低'}电平: 0x{current:02X} -> 0x{new_value:02X}")
        return result
    
    def get_pin_value(self, pin):
        """读取引脚电平值
        
        Args:
            pin: 引脚号 (0-7)
        
        Returns:
            int: PIN_LOW(0) 或 PIN_HIGH(1)，引脚号无效返回-1
        """
        if not 0 <= pin <= 7:
            if self.debug:
                print(f"引脚号无效: {pin}")
            return -1
            
        value = self._read_reg(PCA9557_INPUT_REG)
        return PIN_HIGH if (value & (1 << pin)) else PIN_LOW
    
    def set_pin_polarity(self, pin, polarity):
        """设置引脚极性
        
        Args:
            pin: 引脚号 (0-7)
            polarity: PIN_NON_INVERTED(0) 或 PIN_INVERTED(1)
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        if not 0 <= pin <= 7:
            if self.debug:
                print(f"引脚号无效: {pin}")
            return False
            
        current = self._read_reg(PCA9557_POLARITY_REG)
        if polarity == PIN_NON_INVERTED:
            # 不反转极性 (对应位清0)
            new_value = current & ~(1 << pin)
        else:
            # 反转极性 (对应位置1)
            new_value = current | (1 << pin)
        
        return self._write_reg(PCA9557_POLARITY_REG, new_value)
    
    def read_all_pins(self):
        """读取所有引脚状态并打印
        
        Returns:
            tuple: (input_val, output_val, config_val, polarity_val)
        """
        input_val = self._read_reg(PCA9557_INPUT_REG)
        output_val = self._read_reg(PCA9557_OUTPUT_REG)
        config_val = self._read_reg(PCA9557_CONFIG_REG)
        polarity_val = self._read_reg(PCA9557_POLARITY_REG)
        
        if self.debug:
            print(f"PCA9557状态:")
            print(f"  输入寄存器: 0x{input_val:02X} - {self._format_binary(input_val)}")
            print(f"  输出寄存器: 0x{output_val:02X} - {self._format_binary(output_val)}")
            print(f"  配置寄存器: 0x{config_val:02X} - {self._format_binary(config_val)}")
            print(f"  极性寄存器: 0x{polarity_val:02X} - {self._format_binary(polarity_val)}")
        
        return input_val, output_val, config_val, polarity_val
    
    def write_output(self, pin, value):
        """设置指定引脚的输出电平 (兼容旧方法)
        
        Args:
            pin: 引脚号 (0-7)
            value: 0或1
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        return self.set_pin_value(pin, value)
        
    # 为了向后兼容，保留原来的方法名
    def pin_high(self, pin):
        """设置指定引脚为高电平
        
        Args:
            pin: 引脚号 (0-7)
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        return self.set_pin_value(pin, PIN_HIGH)
    
    def pin_low(self, pin):
        """设置指定引脚为低电平
        
        Args:
            pin: 引脚号 (0-7)
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        return self.set_pin_value(pin, PIN_LOW)
    
    def pin_value(self, pin, value):
        """设置指定引脚的电平
        
        Args:
            pin: 引脚号 (0-7)
            value: 0或1
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        return self.set_pin_value(pin, PIN_HIGH if value else PIN_LOW)

class PCA9557Pin:
    """模拟Pin类，用于PCA9557控制的引脚，兼容machine.Pin接口
    
    此类提供了一个类似machine.Pin的接口，可用于替代普通GPIO引脚，
    特别适合与需要Pin对象的库(如显示屏驱动)配合使用
    """
    def __init__(self, pca9557, pin_num, debug=False):
        """初始化PCA9557Pin
        
        Args:
            pca9557: PCA9557对象
            pin_num: 引脚号 (0-7)
            debug: 是否启用调试输出
        """
        self.pca9557 = pca9557
        self.pin_num = pin_num
        self.debug = debug
        # 默认配置为输出模式
        self.pca9557.set_pin_mode(pin_num, PIN_OUTPUT)
        if self.debug:
            print(f"创建PCA9557Pin - 引脚{pin_num} (输出模式)")
    
    def on(self):
        """设置引脚为高电平
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        return self.pca9557.set_pin_value(self.pin_num, PIN_HIGH)
    
    def off(self):
        """设置引脚为低电平
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        return self.pca9557.set_pin_value(self.pin_num, PIN_LOW)
    
    def value(self, val=None):
        """获取或设置引脚值
        
        Args:
            val: 如果提供，设置引脚值；如果不提供，获取引脚值
            
        Returns:
            如果设置值，返回设置结果(bool)；如果获取值，返回引脚值(int)
        """
        if val is not None:
            return self.pca9557.set_pin_value(self.pin_num, PIN_HIGH if val else PIN_LOW)
        else:
            return self.pca9557.get_pin_value(self.pin_num)
    
    def init(self, mode=None, pull=None):
        """初始化引脚，兼容Pin接口
        
        Args:
            mode: 引脚模式 (1:输入, 0:输出)
            pull: 上下拉设置 (PCA9557不支持，忽略此参数)
            
        Returns:
            self: 返回self，支持链式调用
        """
        if mode is not None:
            # PIN_IN对应PIN_INPUT, PIN_OUT对应PIN_OUTPUT
            pin_mode = PIN_INPUT if mode == 1 else PIN_OUTPUT
            self.pca9557.set_pin_mode(self.pin_num, pin_mode)
        return self

# 常用引脚模式常量，兼容machine.Pin
IN = 1
OUT = 0
PULL_UP = 1
PULL_DOWN = 2
