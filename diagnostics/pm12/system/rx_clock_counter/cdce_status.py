"""CDCE62005 R8 UART wire-word decoding; register payload excludes low address nibble."""
def decode(word):
 if word&15!=8:raise ValueError('Expected register8 wire word')
 payload=word>>4;source=(payload>>25)&7
 return dict(wire_word=f'{word:08x}',payload=f'{payload:07x}',pll_lock_pin=bool(payload&64),selected_source={1:'PRIMARY',2:'SECONDARY',4:'AUX'}.get(source,'UNKNOWN'),source_code=source,status_is_sticky=False)
