library ieee; use ieee.std_logic_1164.all;
entity tb is end; architecture sim of tb is
signal clk:std_logic:='0';
signal a,b,c:std_logic_vector(16 downto 0);
begin
clk <= not clk after 6 ns;
u:entity work.adc_mux generic map(GATE_DIV=>40) port map(clk,'0','0','0',x"123",x"ABC",a(12 downto 0),a(13),a(14),a(15),a(16),open);
v:entity work.adc_mux_original port map(clk,'0','0','0',x"123",x"ABC",b(12 downto 0),b(13),b(14),b(15),b(16),open);
w:entity work.adc_mux port map(clk,'0','0','0',x"123",x"ABC",c(12 downto 0),c(13),c(14),c(15),c(16),open);
process begin
for i in 0 to 999 loop
wait until falling_edge(clk); wait for 1 ns;
assert a(15)=not a(14) report "A/B are not complementary" severity failure;
if i mod 40<20 then assert a(14)='0' report "Wrong low duration" severity failure;
else assert a(14)='1' report "Wrong high duration" severity failure; end if;
assert a(13 downto 0)=b(13 downto 0) and a(16)=b(16) report "ADC mux/CLK40/DV changed" severity failure;
assert c=b report "Default divider not backward compatible" severity failure;
end loop;
report "DIV40_COMPLEMENTARY_50PCT_AND_CLOCK_PRESERVATION_PASS";
std.env.stop; wait;
end process;
end;
