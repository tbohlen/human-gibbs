import unittest
from numpy import *
from numpy.testing import assert_approx_equal
import analysis

class TestDiscreteTruncT(unittest.TestCase):
    def test_default_loc_and_scale(self):
        # set up test
        x = eye(2)
        result = analysis.discrete_trunc_t_logpdf(x, 1, range(2))
        
        # check that the values that should be the same are the same
        assert_approx_equal(result[0,0], result[1,1])
        assert_approx_equal(result[0,1], result[1,0])

        # check that values that should be larger are larger
        self.assertTrue(result[0,0] < result[1,0])

        # check that the is properly normalized
        assert_approx_equal(exp(result[0,0]) + exp(result[1,0]), 1)

    def test_normalization(self):
        # set up
        x = arange(12).reshape((3,4))
        result = analysis.discrete_trunc_t_logpdf(x, 4, range(12))

        # make sure normalized
        assert_approx_equal(sum(exp(result)), 1)

    def test_sanity_checks(self):
        # test change in mean
        result0 = analysis.discrete_trunc_t_logpdf([0,1], 1, range(2))
        result1 = analysis.discrete_trunc_t_logpdf([0,1], 1, range(2), loc=1)

        assert_approx_equal(result0[0], result1[1])
        assert_approx_equal(result0[1], result1[0])

        # test change in scale
        result2 = analysis.discrete_trunc_t_logpdf([0,1], 1, range(2), scale=1)
        result3 = analysis.discrete_trunc_t_logpdf([0,1], 1, range(2), scale=10)

        self.assertTrue(result2[0] > result3[0])
        self.assertTrue(result2[1] < result3[1])
        
    def test_array_mean(self):
        result = analysis.discrete_trunc_t_logpdf([0,1], 1, range(2), loc=[0,1])

        assert_approx_equal(result[0], result[1])

    def test_array_scale(self):
        result = analysis.discrete_trunc_t_logpdf([0,0], 1, range(2), scale=[1,10])

        self.assertTrue(result[0] > result[1])


class TestLogLikelihood(unittest.TestCase):
    def setUp(self):
        # create images and add them to the image_matrices dict
        self.black_image = zeros((2,2))
        self.black_id = 'black'
        self.white_image = ones((2,2)) * 255
        self.white_id = 'white'
        self.light_grey_image = ones((2,2)) * 191
        self.light_grey_id = 'light_grey'
        self.dark_grey_image = ones((2,2)) * 63
        self.dark_grey_id = 'dark_grey'
        self.mostly_black_image = self.black_image.copy()
        self.mostly_black_image[0,0] = 255
        self.mostly_black_id = 'mostly_black'
        self.mostly_white_image = self.white_image.copy()
        self.mostly_white_image[0,0] = 0
        self.mostly_white_id = 'mostly_white'
        analysis.image_matrices[self.black_id] = self.black_image
        analysis.image_matrices[self.white_id] = self.white_image
        analysis.image_matrices[self.light_grey_id] = self.light_grey_image
        analysis.image_matrices[self.dark_grey_id] = self.dark_grey_image
        analysis.image_matrices[self.mostly_black_id] = self.mostly_black_image
        analysis.image_matrices[self.mostly_white_id] = self.mostly_white_image

        # create a uniform partition
        self.black_group = 0
        self.white_group = 1
        self.uniform_partition = {self.black_id: self.black_group,
                                  self.white_id: self.white_group}

        # create a mixed partition
        self.mixed_partition = {self.black_id: self.black_group,
                                self.mostly_black_id: self.black_group,
                                self.dark_grey_id: self.black_group,
                                self.white_id: self.white_group,
                                self.mostly_white_id: self.white_group,
                                self.light_grey_id: self.white_group}

    def test_solid_images_uniform(self):
        black_to_black = analysis.log_likelihood(self.uniform_partition,
                                                 self.black_group,
                                                 self.black_id)
        black_to_white = analysis.log_likelihood(self.uniform_partition,
                                                 self.white_group,
                                                 self.black_id)
        white_to_white = analysis.log_likelihood(self.uniform_partition,
                                                 self.white_group,
                                                 self.white_id)
        white_to_black = analysis.log_likelihood(self.uniform_partition,
                                                 self.black_group,
                                                 self.white_id)

        assert_approx_equal(black_to_black, white_to_white)
        assert_approx_equal(black_to_white, white_to_black)
        self.assertTrue(black_to_black > black_to_white)

    def test_grey_images_uniform(self):
        light_grey_to_black = analysis.log_likelihood(self.uniform_partition,
                                                      self.black_group,
                                                      self.light_grey_id)
        light_grey_to_white = analysis.log_likelihood(self.uniform_partition,
                                                      self.white_group,
                                                      self.light_grey_id)
        dark_grey_to_white = analysis.log_likelihood(self.uniform_partition,
                                                     self.white_group,
                                                     self.dark_grey_id)
        dark_grey_to_black = analysis.log_likelihood(self.uniform_partition,
                                                     self.black_group,
                                                     self.dark_grey_id)

        assert_approx_equal(light_grey_to_black, dark_grey_to_white, significant=5)
        assert_approx_equal(light_grey_to_white, dark_grey_to_black, significant=5)
        self.assertTrue(light_grey_to_white > light_grey_to_black)

    def test_mostly_uniform(self):
        mostly_black_to_black = analysis.log_likelihood(self.uniform_partition,
                                                        self.black_group,
                                                        self.mostly_black_id)
        mostly_black_to_white = analysis.log_likelihood(self.uniform_partition,
                                                        self.white_group,
                                                        self.mostly_black_id)
        mostly_white_to_white = analysis.log_likelihood(self.uniform_partition,
                                                        self.white_group,
                                                        self.mostly_white_id)
        mostly_white_to_black = analysis.log_likelihood(self.uniform_partition,
                                                        self.black_group,
                                                        self.mostly_white_id)

        assert_approx_equal(mostly_black_to_black, mostly_white_to_white)
        assert_approx_equal(mostly_black_to_white, mostly_white_to_black)
        self.assertTrue(mostly_black_to_black > mostly_black_to_white)
        
    def test_solid_images_mixed(self):
        black_to_black = analysis.log_likelihood(self.mixed_partition,
                                                 self.black_group,
                                                 self.black_id)
        black_to_white = analysis.log_likelihood(self.mixed_partition,
                                                 self.white_group,
                                                 self.black_id)
        white_to_white = analysis.log_likelihood(self.mixed_partition,
                                                 self.white_group,
                                                 self.white_id)
        white_to_black = analysis.log_likelihood(self.mixed_partition,
                                                 self.black_group,
                                                 self.white_id)

        assert_approx_equal(black_to_black, white_to_white)
        assert_approx_equal(black_to_white, white_to_black)
        self.assertTrue(black_to_black > black_to_white)

    def test_grey_images_mixed(self):
        light_grey_to_black = analysis.log_likelihood(self.mixed_partition,
                                                      self.black_group,
                                                      self.light_grey_id)
        light_grey_to_white = analysis.log_likelihood(self.mixed_partition,
                                                      self.white_group,
                                                      self.light_grey_id)
        dark_grey_to_white = analysis.log_likelihood(self.mixed_partition,
                                                     self.white_group,
                                                     self.dark_grey_id)
        dark_grey_to_black = analysis.log_likelihood(self.mixed_partition,
                                                     self.black_group,
                                                     self.dark_grey_id)

        assert_approx_equal(light_grey_to_black, dark_grey_to_white, significant=5)
        assert_approx_equal(light_grey_to_white, dark_grey_to_black, significant=5)
        self.assertTrue(light_grey_to_white > light_grey_to_black)

    def test_mostly_mixed(self):
        mostly_black_to_black = analysis.log_likelihood(self.mixed_partition,
                                                        self.black_group,
                                                        self.mostly_black_id)
        mostly_black_to_white = analysis.log_likelihood(self.mixed_partition,
                                                        self.white_group,
                                                        self.mostly_black_id)
        mostly_white_to_white = analysis.log_likelihood(self.mixed_partition,
                                                        self.white_group,
                                                        self.mostly_white_id)
        mostly_white_to_black = analysis.log_likelihood(self.mixed_partition,
                                                        self.black_group,
                                                        self.mostly_white_id)

        assert_approx_equal(mostly_black_to_black, mostly_white_to_white)
        assert_approx_equal(mostly_black_to_white, mostly_white_to_black)
        self.assertTrue(mostly_black_to_black > mostly_black_to_white)

        
if __name__ == '__main__':
    unittest.main()


    
