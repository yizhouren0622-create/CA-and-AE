"""Regression checks for semantic grouping in offline mathematical typography."""
import unittest
import xml.etree.ElementTree as ET
from math_typesetting import render_math,format_text,raw_to_tex,identifier,NS

def tree(tex):return ET.fromstring(render_math(tex))
def alltags(e,t):return list(e.iter('{'+NS+'}'+t))
def value(e):return ''.join(e.itertext())

class MathTypography(unittest.TestCase):
 def test_simulator_version_is_prose_not_a_subscript(self):
  for name in ['ngspice47','LTspice17','PSpice23','IRF9512','IRF832','IRF840','IRF9510','CMOS']:
   rendered=format_text('Verified with '+name+'.','en')
   self.assertIn(name,rendered)
   self.assertNotIn('<msub',rendered)
  self.assertIn('<msub',format_text('R1','en'))
 def test_prose_component_names_have_subscripts(self):
  for name,sub in [('Rb','b'),('Rac','ac'),('Kn','n'),('Ri','i')]:
   e=tree(identifier(name));self.assertEqual(value(alltags(e,'msub')[0][1]),sub)
   self.assertIn('<math',format_text('Use '+name+' here.','en'))
  self.assertEqual(identifier('Re'),r'\operatorname{Re}')
 def test_bias_point_names_are_one_subscript(self):
  for name,sub in [('VGSQ','GSQ'),('VCEQ','CEQ'),('ICQ','CQ')]:
   e=tree(identifier(name));self.assertEqual(len(alltags(e,'msub')),1)
   self.assertEqual(value(alltags(e,'msub')[0][1]),sub)
 def test_fraction_precedence_and_nested_sums(self):
  e=tree(r'\frac{v_{i1}/R_1+v_{i2}/R_2}{1/R_1+1/R_2}')
  f=alltags(e,'mfrac');self.assertEqual(len(f),5)
  self.assertEqual(len(alltags(f[0][0],'mfrac')),2)
  self.assertEqual(len(alltags(f[0][1],'mfrac')),2)
  self.assertIn('+',value(f[0][0]));self.assertIn('+',value(f[0][1]))
 def test_exponential_division_stays_in_exponent(self):
  e=tree(raw_to_tex('e^(−t/20ms)'))
  p=alltags(e,'msup')[0]
  self.assertEqual(value(p[0]),'e');f=alltags(p[1],'mfrac')[0]
  self.assertEqual(value(f[0]),'t');self.assertEqual(value(f[1]),'20ms')
 def test_quantity_power_applies_only_to_unit(self):
  e=tree(raw_to_tex('650 cm²/(V·s)'))
  f=alltags(e,'mfrac')[0];p=alltags(f[0],'msup')[0]
  self.assertEqual(value(p[0]),'cm');self.assertEqual(value(p[1]),'2')
  self.assertEqual(value(f[0]),'650cm2')
 def test_fractional_result_keeps_its_unit_outside(self):
  e=tree(raw_to_tex('14/23 A'))
  f=alltags(e,'mfrac')[0]
  self.assertEqual(value(f[0]),'14');self.assertEqual(value(f[1]),'23')
  self.assertTrue(value(e).endswith('A'))
 def test_result_unit_after_parenthesized_denominator(self):
  e=tree(raw_to_tex('V_A=18(R−1)/(R+4) V'))
  f=alltags(e,'mfrac')[0]
  self.assertEqual(value(f[1]),'(R+4)')
  self.assertTrue(value(e).endswith('V'))
 def test_differential_is_not_an_integrand_subscript(self):
  e=tree(raw_to_tex('∫v_i2dτ'))
  self.assertEqual(value(alltags(e,'msub')[0][1]),'i2')
  self.assertTrue(value(e).endswith('dτ'))
 def test_sequential_division_is_left_associative(self):
  f=alltags(tree('a/b/c'),'mfrac')[0]
  self.assertEqual(value(f[1]),'c');self.assertEqual(len(alltags(f[0],'mfrac')),1)
 def test_numeric_nested_fractions_preserve_denominator_sum(self):
  f=alltags(tree(r'\frac{76/7}{10/7+4}'),'mfrac')[0]
  self.assertEqual(len(alltags(f[0],'mfrac')),1)
  self.assertEqual(len(alltags(f[1],'mfrac')),1);self.assertTrue(value(f[1]).endswith('+4'))
 def test_cases_rows_preserved(self):
  self.assertEqual(len(alltags(tree(r'\begin{cases}t/2&t<0\\1/2&t=0\\t/3&t>0\end{cases}'),'mtr')),3)
 def test_hat_is_an_accent_not_raw_caret(self):
  e=tree(r'\hat{I}_1=\hat{U}_2/R')
  accents=alltags(e,'mover')
  self.assertEqual(len(accents),2)
  self.assertTrue(all(value(a[1])=='ˆ' for a in accents))
  self.assertNotIn('^',value(e))
 def test_compound_subscripts_and_adjacent_factors(self):
  for raw,expected in [('v_AK',r'v_{\mathrm{AK}}'),('g_mR_s',r'g_{\mathrm{m}}R_{\mathrm{s}}'),('K_pV_OV',r'K_{\mathrm{p}}V_{\mathrm{OV}}'),('g_mR₁',r'g_{\mathrm{m}}R_{1}')]:
   self.assertEqual(identifier(raw),expected)
 def test_phasors_supplies_and_primes(self):
  for raw in ['İ_L₁','ω_L','μ_n','v_s′','V_+','V_−','r_bb′']:
   e=tree(raw_to_tex(raw));self.assertTrue(alltags(e,'msub') or alltags(e,'msubsup'),raw)
  self.assertTrue(alltags(tree(raw_to_tex('İ_L₁')),'mover'))
 def test_scientific_notation_and_complex_numbers(self):
  self.assertEqual(value(alltags(tree(raw_to_tex('1e−3 A')),'msup')[0]),'10−3')
  self.assertFalse(alltags(tree(raw_to_tex('j100')),'msub'))
 def test_prose_ids_and_literal_names(self):
  for word in ['An','At','In','If','It','sum','PDF','AC','DC']:self.assertIsNone(identifier(word))
  text=format_text('An ideal op amp at Fig. 2.4.2a; save UA741_40mA.lib.','en')
  self.assertIn('An ideal',text);self.assertIn('2.4.2a',text)
  self.assertIn('<code>UA741_40mA.lib</code>',text)
 def test_visible_legacy_formulas_and_units(self):
  with self.assertRaises(ValueError):render_math('\x0crac{1}{2}')
  for raw in ['RC·dv_p/dt=v_i2−v_p','İ_L₁=(√2/2)∠−45° A','K′_nW/L=500 μA/V²','2V_TN','v_P−v_N','dB/decade','rad/s']:
   html=format_text(raw);self.assertIn('<math',html,raw)
   self.assertNotIn('_',html);self.assertNotIn('<mo>/</mo>',html)
   self.assertNotIn(' and ',html)

if __name__=='__main__':unittest.main()
