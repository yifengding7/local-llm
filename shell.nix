# 为不使用flakes的用户提供兼容性
(builtins.getFlake (toString ./.)).devShells.${builtins.currentSystem}.default