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

import torch
import torch.nn as nn


class Floor(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        return x.floor()

    @staticmethod
    def backward(ctx, grad):
        return grad


class Round(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        return (x + 0.5 * torch.sign(x)).trunc()

    @staticmethod
    def backward(ctx, grad):
        return grad


class UniformQuantization(nn.Module):
    """See `this page <https://sp-nitech.github.io/sptk/latest/main/quantize.html>`_
    for details. The gradient is copied from the next module.

    Parameters
    ----------
    abs_max : float > 0 [scalar]
        Absolute maximum value of input.

    n_bit : int >= 1 [scalar]
        Number of quantization bits.

    quantizer : ['mid-rise', 'mid-tread']
        Quantizer.

    """

    def __init__(self, abs_max=1, n_bit=8, quantizer="mid-rise"):
        super(UniformQuantization, self).__init__()

        assert 0 < abs_max
        assert 1 <= n_bit

        self.abs_max = abs_max
        self.const = self._precompute_const(n_bit, quantizer)

    def forward(self, x):
        """Quantize input.

        Parameters
        ----------
        x : Tensor [shape=(...,)]
            Input.

        Returns
        -------
        Tensor [shape=(...,)]
            Quantized input.

        Examples
        --------
        >>> x = diffsptk.ramp(-4, 4)
        >>> quantize = diffsptk.UniformQuantization(4, 2)
        >>> y = quantize(x).int()
        >>> y
        tensor([0, 0, 1, 1, 2, 2, 3, 3, 3], dtype=torch.int32)

        """
        return self._forward(x, self.abs_max, *self.const)

    @staticmethod
    def _forward(x, abs_max, level, func):
        y = func(x * (level / (2 * abs_max)))
        y = torch.clip(y, min=0, max=level - 1)
        return y

    @staticmethod
    def _func(x, abs_max, n_bit, quantizer):
        const = UniformQuantization._precompute_const(n_bit, quantizer)
        return UniformQuantization._forward(x, abs_max, *const)

    @staticmethod
    def _precompute_const(n_bit, quantizer):
        if quantizer == 0 or quantizer == "mid-rise":
            level = 1 << n_bit
            return level, lambda x: Floor.apply(x + level // 2)
        elif quantizer == 1 or quantizer == "mid-tread":
            level = (1 << n_bit) - 1
            return level, lambda x: Round.apply(x + (level - 1) // 2)
        raise ValueError(f"quantizer {quantizer} is not supported.")
