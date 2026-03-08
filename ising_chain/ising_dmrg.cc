/**
 * 一次元イジング鎖の基底状態エネルギーと波動関数を DMRG で求める
 *
 * ハミルトニアン: H = -J Σ_i S^z_i S^z_{i+1}
 *
 * - J > 0 (強磁性): 基底状態は全スピン同方向（|↑↑↑...⟩ または |↓↓↓...⟩）
 * - J < 0 (反強磁性): 基底状態は Néel 状態（|↑↓↑↓...⟩）
 */

#include "itensor/all.h"
#include "itensor/util/print_macro.h"
#include <chrono>
#include <fstream>
#include <cstdlib>

using namespace itensor;

int main(int argc, char *argv[])
{
    // ========== パラメータ ==========
    int N = 20;           // サイト数（デフォルト）
    Real J = 1.0;         // 結合定数 (J>0: 強磁性, J<0: 反強磁性)

    if (argc >= 2)
        N = std::atoi(argv[1]);
    if (argc >= 3)
        J = std::atof(argv[2]);

    println("========================================");
    println("一次元イジング鎖 DMRG");
    println("========================================");
    printfln("サイト数 N = %d", N);
    printfln("結合定数 J = %.2f", J);
    if (J > 0)
        println("(強磁性: 基底状態は全スピン同方向)");
    else
        println("(反強磁性: 基底状態は Néel 状態)");
    println();

    // ========== (1) SiteSet: スピン1/2鎖 ==========
    auto sites = SpinHalf(N, {"ConserveQNs=", false});

    // ========== (2) MPO: イジングハミルトニアン ==========
    // H = -J Σ_i S^z_i S^z_{i+1}
    auto ampo = AutoMPO(sites);
    for (int j = 1; j < N; ++j)
    {
        ampo += -J, "Sz", j, "Sz", j + 1;
    }
    auto H = toMPO(ampo);

    // ========== (3) 初期状態 ==========
    // ランダムな初期配置（局所極小を避けるため）
    auto psi0 = randomMPS(sites);

    printfln("初期エネルギー = %.10f", inner(psi0, H, psi0));

    // ========== (4) Sweeps: DMRG パラメータ ==========
    auto sweeps = Sweeps(10);
    sweeps.maxdim() = 10, 20, 50, 100, 100, 200, 200, 200, 200, 200;
    sweeps.cutoff() = 1E-12;
    sweeps.niter() = 2;

    // ========== (5) DMRG 実行 ==========
    auto t_start = std::chrono::high_resolution_clock::now();
    auto [energy, psi] = dmrg(H, psi0, sweeps, {"Silent", true});
    auto t_end = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(t_end - t_start).count();

    println();
    println("========================================");
    printfln("基底状態エネルギー = %.12f", energy);
    printfln("(inner で検証)       = %.12f", inner(psi, H, psi));
    println("========================================");

    // ========== (6) 波動関数の性質: 各サイトの <S^z> ==========
    println();
    println("各サイトの <S^z> (磁化プロファイル):");
    println("サイト  <Sz>");
    println("------ --------");

    for (int j = 1; j <= N; ++j)
    {
        psi.position(j);
        auto ket = psi(j);
        auto bra = dag(prime(ket, "Site"));
        auto Sz_op = sites.op("Sz", j);
        auto sz = (bra * Sz_op * ket).real();
        printfln("  %3d   %+.6f", j, sz);
    }

    // 理論値との比較（強磁性 J>0, 開端）
    // 基底状態: 全スピン同方向 → E = -J * (N-1) * (1/2)*(1/2) = -J(N-1)/4
    Real E_exact = -J * (N - 1) / 4.0;
    printfln("\n理論値 (強磁性, 全スピン同方向): E = -J(N-1)/4 = %.10f", E_exact);
    if (J > 0)
        printfln("誤差: %.2e", std::abs(energy - E_exact));
    printfln("DMRG実行時間: %.4f 秒", elapsed);
    printfln("TIME_SECONDS: %.6f", elapsed);
    printfln("ENERGY: %.12f", energy);

    // ========== (7) 可視化用データをファイルに出力 ==========
    const char *outfile = "ising_data.csv";
    std::ofstream ofs(outfile);
    ofs << "N,J,energy" << std::endl;
    ofs << N << "," << J << "," << energy << std::endl;
    ofs << "site,Sz" << std::endl;

    std::vector<Real> sz_vals(N);
    for (int j = 1; j <= N; ++j)
    {
        psi.position(j);
        auto ket = psi(j);
        auto bra = dag(prime(ket, "Site"));
        auto Sz_op = sites.op("Sz", j);
        auto sz = (bra * Sz_op * ket).real();
        sz_vals[j - 1] = sz;
        ofs << j << "," << sz << std::endl;
    }

    // 相関関数 ⟨S^z_i S^z_j⟩
    auto corr = correlationMatrix(psi, sites, "Sz", "Sz", range1(1, N));
    ofs << "correlation_matrix" << std::endl;
    for (size_t i = 0; i < corr.size(); ++i)
    {
        for (size_t j = 0; j < corr[i].size(); ++j)
        {
            ofs << (j > 0 ? "," : "") << corr[i][j];
        }
        ofs << std::endl;
    }
    ofs.close();

    printfln("\n可視化用データを %s に出力しました。", outfile);
    println("  python visualize.py で可視化できます。");

    return 0;
}
