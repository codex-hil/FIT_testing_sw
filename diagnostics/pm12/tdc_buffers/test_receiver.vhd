-- Serial receiver test ONLY. Coarse capture and FIFO are stubbed deliberately.
library ieee;
use ieee.std_logic_1164.all;
entity pin_capt is
  port(pin_in: in std_logic; pin_out: out std_logic; clk600,clk600_90,clk300: in std_logic;
       str: out std_logic; ptime: out std_logic_vector(2 downto 0));
end;
architecture stub of pin_capt is
begin pin_out<=pin_in; str<='0'; ptime<="000"; end;

library ieee;
use ieee.std_logic_1164.all;
entity TDC_FIFO is
  port(clk,srst: in std_logic; din: in std_logic_vector(5 downto 0);
       wr_en,rd_en: in std_logic; dout: out std_logic_vector(5 downto 0); full,empty: out std_logic);
end;
architecture stub of TDC_FIFO is
begin dout<="101010"; full<='0'; empty<='0'; end;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity test_receiver is end;
architecture test of test_receiver is
  signal clk: std_logic:='0';
  signal clk300: std_logic:='0';
  signal rstr: std_logic:='0';
  signal rdata: std_logic:='0';
  signal locked: std_logic:='0';
  signal valid,ready: std_logic;
  signal raw: std_logic_vector(12 downto 0);
begin
  clk<=not clk after 5 ns;
  clk300<=not clk300 after 1.667 ns;
  dut: entity work.TDCCHAN port map(
    pin_in=>'0',pin_out=>open,clk300=>clk300,clk600=>clk,clk600_90=>clk,
    reset=>'0',tdcclk=>clk,rstr=>rstr,rdata=>rdata,tdc_count=>"0000",bc_time=>"0000000",
    tdc_out=>open,tdc_rdy=>ready,tdc_raw=>raw,tdc_raw_lock=>locked,diag_raw_valid=>valid);
  process
    variable bits: std_logic_vector(6 downto 0);
    variable previous: std_logic_vector(12 downto 0);
  begin
    for lockmode in 0 to 1 loop
      for value in 0 to 127 loop
        bits:=std_logic_vector(to_unsigned(value,7)); previous:=raw;
        if lockmode=1 then locked<='1'; else locked<='0'; end if;
        rstr<='1';
        wait until rising_edge(clk); wait until rising_edge(clk); wait for 1 ns;
        rstr<='0';
        wait until rising_edge(clk); wait for 1 ns; -- falling-strobe detection
        assert valid='0' severity failure;
        for i in 0 to 6 loop
          rdata<=bits(i);
          wait until rising_edge(clk); wait for 1 ns;
          assert valid='0' report "commit pulse before complete raw word" severity failure;
          wait until falling_edge(clk); wait for 1 ns;
          if i=5 then
            assert ready='1' report "original early-ready timing changed" severity failure;
          end if;
        end loop;
        wait until rising_edge(clk); wait for 1 ns;
        if lockmode=0 then
          assert valid='1' report "missing original raw-commit pulse" severity failure;
          assert raw=("101010" & bits) report "serial bit order/raw composition incorrect" severity failure;
        else
          assert valid='0' report "raw lock ignored" severity failure;
          assert raw=previous report "raw register changed while locked" severity failure;
        end if;
        wait until rising_edge(clk); wait for 1 ns;
        assert valid='0' report "raw-commit pulse not one cycle" severity failure;
        assert ready='1' report "original ready must remain asserted" severity failure;
      end loop;
    end loop;
    report "PASS original serial receiver:128 values, raw commit timing, early/sticky ready and raw lock; coarse/FIFO STUBBED" severity note;
    std.env.stop;
    wait;
  end process;
end;
