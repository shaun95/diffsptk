# ------------------------------------------------------------------------ #
# Copyright 2022 SPTK Working Group                                        #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License");          #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http://www.apache.org/licenses/LICENSE-2.0                           #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
# ------------------------------------------------------------------------ #

import numpy as np
import torch
import torch.nn as nn


class MelCepstrumToMLSADigitalFilterCoefficients(nn.Module):
    def __init__(self, cep_order, alpha):
        """Initialize module.

        Parameters
        ----------
        cep_order : int >= 1 [scalar]
            Order of cepstrum, M.

        alpha : float [-1 < alpha < 1]
            Frequency warping factor.

        """
        super(MelCepstrumToMLSADigitalFilterCoefficients, self).__init__()

        self.cep_order = cep_order
        self.alpha = alpha

        assert 0 <= self.cep_order
        assert abs(self.alpha) < 1

        # Make transform matrix.
        A = np.eye(self.cep_order + 1, dtype=np.float32)
        a = 1
        for m in range(1, len(A)):
            a *= -self.alpha
            np.fill_diagonal(A[:, m:], a)

        self.register_buffer("A", torch.from_numpy(A).t())

    def forward(self, c):
        """Convert mel-cepstrum to MLSA filter coefficients.

        Parameters
        ----------
        c : Tensor [shape=(..., M+1)]
            Mel-cepstral coefficients.

        Returns
        -------
        b : Tensor [shape=(..., M+1)]
            MLSA filter coefficients.

        """
        b = torch.matmul(c, self.A if c.dtype == self.A.dtype else self.A.double())
        return b
