from ro_randomizer.script import *
from ror_tests.base_tests import *
import unittest

testscript = """
// test comment
dic_fild02,241,31,4	script	Transport Device#04	10007,{
	mes "Do you wish to enter the Dimensional Gap?";
	next; // test comment
	switch(select("Yes:No")) {
	case 1:
		close2;
		warp "dali",41,134;
		end;
	case 2:
		close;
	}
}

/*
test block comment
*/

dali,149,82,0	warp	dg001	2,2,mid_camp,210,289
dali,122,48,0	warp	dg002	2,2,moc_fild22b,227,200
dali,38,87,0	warp	dg003	2,2,bif_fild01,318,155
dali,34,139,0	warp	dg004	2,2,dic_fild02,237,32

dali,64,129,0	warp	#dali_to_dali02	1,1,dali02,66,101
dali02,66,97,0	warp	#dali02_to_dali	1,1,dali,64,125
"""

goalscript = """dic_fild02,241,31,4	script	Transport Device#04	10007,{
	mes "Do you wish to enter the Dimensional Gap?";
	next;
	switch(select("Yes:No")) {
	case 1:
		close2;
		warp "dali",41,134;
		end;
	case 2:
		close;
	}
}
dali,149,82,0	warp	dg001	2,2,mid_camp,210,289
dali,122,48,0	warp	dg002	2,2,moc_fild22b,227,200
dali,38,87,0	warp	dg003	2,2,bif_fild01,318,155
dali,34,139,0	warp	dg004	2,2,dic_fild02,237,32
dali,64,129,0	warp	#dali_to_dali02	1,1,newmap,1,2
dali02,66,97,0	warp	#dali02_to_dali	1,1,dali,64,125
"""

class TestScriptParsing(BaseTestCase):
    def test_script(self):
        s = parse_script(testscript)

        dali_to_dali02 = s[5]
        self.assertEqual(dali_to_dali02.content, "dali,64,129,0	warp	#dali_to_dali02	1,1,dali02,66,101")
        substr = testscript[dali_to_dali02.start_idx:dali_to_dali02.end_idx]
        self.assertEqual(dali_to_dali02.content, substr)

        # test modifying statements in the script
        dali_to_dali02.args[3][2] = 'newmap'
        dali_to_dali02.args[3][3] = 1
        dali_to_dali02.args[3][4] = 2

        # test writing the script out to a string
        self.assertEqual(repr(s), goalscript)

