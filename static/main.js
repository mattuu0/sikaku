//解答欄
const kaitouran = document.getElementById("kaitouran");

//答え合わせボタン
const check_anser_btn = document.getElementById("check_anser_btn");

//結果ボタン
const reuslt_text = document.getElementById("reuslt_text");

//ロード中画面
const LoadScreen = document.getElementById("LoadScreen");

//メインコンテンツ
const main_content = document.getElementById("main_content");

//ロード中のメッセージ
const overlay_message = document.getElementById("overlay_message");

//ロード画面を表示する
function show_load() {
    LoadScreen.style.display = "flex";
    main_content.style.overflowY = "hidden";
    document.addEventListener("scroll", noscroll, { passive: false });
    document.addEventListener("touchmove", noscroll, { passive: false });
}

//ロード画面を隠す
function hide_load() {
    document.removeEventListener("scroll", noscroll);
    document.removeEventListener("touchmove", noscroll);
    LoadScreen.style.display = "none";
    main_content.style.overflowY = "auto";
}

//最初の画面を隠す
hide_load();

//回答データ
let datas = {};

//問題名
let mondai_name = "";

//待機する関数
async function wait(milsecond) {
    return new Promise(resolve => setTimeout(resolve, milsecond));
}

//スクロールイベントを無効化する
function noscroll(evt) {
    evt.preventDefault();
}

//問題を表示する関数
function show_mondai(mondai_data, clear_all) {
    try {
        //解答欄を更新する場合
        if (clear_all) {
            datas = {};

            //解答欄をすべて削除する
            while (kaitouran.firstChild) {
                kaitouran.removeChild(kaitouran.lastChild);
            }
        }

        //問題データを回す
        for (const question_data of mondai_data) {
            //追加する列
            const addtr = document.createElement("tr");

            //問題番号を取得する
            const question_number = question_data["num"];

            //問題番号を入れる
            addtr.id = question_number;

            //解答欄を更新する場合
            if (clear_all) {
                //解答欄を追加する
                addtr.insertAdjacentHTML("beforeend", `
                    <th scope="row" class="d-flex" style="width: 100%;">
                        <p>${question_number}</p>
                        <div class="form-check mx-3">
                            <input class="form-check-input" type="checkbox" value="" id="after_check_${question_number}">
                            <label style="user-select: none; white-space: nowrap;" class="form-check-label" for="after_check_${question_number}">
                                後で見直すためにチェックする
                            </label>
                        </div>
                    </th>
                    <td style="width: 25%;">
                        <select class="form-select" id="input_answer">
                            <option selected value="-1">未回答</option>
                            <option value="0">ア</option>
                            <option value="1">イ</option>
                            <option value="2">ウ</option>
                            <option value="3">エ</option>
                        </select>
                    </td>
                    <td style="width: 25%;">
                        <select class="form-select" id="mohan_answer" style="white-space: nowrap;" disabled>
                            <option value="-1">---</option>
                            <option value="0">ア</option>
                            <option value="1">イ</option>
                            <option value="2">ウ</option>
                            <option value="3">エ</option>
                        </select>
                    </td>
                    <td id="result" style="white-space: nowrap;">
                        ---
                    </td>
                `);

                //解答欄を追加する
                kaitouran.appendChild(addtr);
            }

            //答えを番号に変更する
            let selctindex = 0;
            switch (question_data["ans"]) {
                case "ア":
                    selctindex = 1;
                    break;
                case "イ":
                    selctindex = 2;
                    break;
                case "ウ":
                    selctindex = 3;
                    break;
                case "エ": 
                    selctindex = 4;
                    break;
            }

            //データを更新する場合
            if (clear_all) {
                //情報を更新する
                datas[question_data["num"]] = {
                    answer_area: addtr.querySelector("#input_answer"),                  //答え入力エリア
                    mohan_area: addtr.querySelector("#mohan_answer"),                   //模範解答エリア
                    check_area: addtr.querySelector(`#after_check_${question_number}`), //見直すためのチェックボタン
                    result_area: addtr.querySelector("#result"),                        //結果表示エリア
                    basetr: addtr,                                                      //追加した列
                    answer_data: selctindex                                             //答えデータ (インデックス)
                }
            } else {
                //列を削除する
                addtr.remove();

                try {
                    // 
                    datas[question_data["num"]]["answer_data"] = selctindex;
                } catch (ex) {
                    console.log(ex);
                }
            }
        }
    } catch (ex) {
        console.log(ex);
    }

    //ロード画面をかくす
    hide_load();
}

//レポート文字列
let report_str = "";

//採点ボタンが押されたとき
check_anser_btn.addEventListener("click", async (evt) => {
    //表示する
    overlay_message.innerText = "採点しています";

    //結果文字列を空にする
    report_str = "";

    //問題数をカウントする
    let max_size = 0;

    //結果をリセットする
    for (let key in datas) {
        const check_data = datas[key];
        check_data.result_area.innerText = "---";
        check_data.mohan_area.selectedIndex = -1;
        check_data.basetr.classList.remove(...check_data.basetr.classList);
        max_size++;
    }

    //正解数を初期化する
    let okcount = 0;

    //ロード画面を表示する
    show_load();

    //データを回す
    for (let key in datas) {
        //確認するデータ
        const check_data = datas[key];

        //ユーザーが選択した番号
        let select_index = check_data.answer_area.selectedIndex;
        
        //正解しているか
        const isok = select_index == check_data.answer_data;

        if (isok) {
            //正解している場合
            check_data.result_area.innerText = "正解";
            okcount++;
        } else {
            //不正解の場合
            check_data.result_area.innerText = "不正解";
            check_data.basetr.classList.add("table-danger");
        }

        //模範解答を設定する
        check_data.mohan_area.selectedIndex = check_data.answer_data;

        //模範解答のインデックス
        let mohan_index = check_data.mohan_area.selectedIndex;

        //スクロールする
        const scrolly = check_data.result_area.offsetTop;
        main_content.scrollTo(0, scrolly);

        await wait(50);

        //レポート用の文字列
        let checked_str = "";
        if (check_data.check_area.checked) {
            checked_str = "checked";
        }

        //間違えたときのやつ
        let is_danger_str = "";
        if (!isok) {
            is_danger_str = "table-danger";
        }

        //正解か不正解か
        let result_str = ""
        if (isok) {
            result_str = "正解";
        } else {
            result_str = "不正解";
        }

        report_str += `
        <tr class="${is_danger_str}">
            <th scope="row" class="d-flex" style="width: 100%;">
                <p>${key}</p>
                <div class="form-check mx-3">
                    <input class="form-check-input" type="checkbox" ${checked_str}>
                    <label style="user-select: none; white-space: nowrap;" class="form-check-label" for="after_check_60">
                        後で見直すためにチェックする
                    </label>
                </div>
            </th>
            <td style="width: 25%;">
                <select class="form-select" id="input_answer" disabled>
                    <option selected>${check_data.mohan_area.options[select_index].text}</option>
                </select>
            </td>
            <td style="width: 25%;">
                <select class="form-select" id="mohan_answer" style="white-space: nowrap;" disabled>
                    <option selected>${check_data.mohan_area.options[mohan_index].text}</option>
                </select>
            </td>
            <td id="result" style="white-space: nowrap;">
                ${result_str}
            </td>
        </tr>`
    }

    //結果文字列
    const result_txt = `${max_size}問中 / ${okcount}問正解\t正解率 : ${okcount / max_size * 100}%`;
    reuslt_text.innerText = result_txt;

    //レポートのHtml
    report_str = out_report(report_str,result_txt);

    //ロード画面を隠す
    hide_load();

    //スクロールする
    const scrolly = reuslt_text.offsetTop;
    main_content.scroll(0, scrolly);
});

if (!debug_mode) {
    window.onbeforeunload = function(evt) {
        evt = evt || window.event
        return evt.returnValue = '本当に移動してもいいんですか?';
    }
}

//基本情報問題を選ぶ
const fe_menjo_mondai_select = document.querySelector("#fe_menjo_mondai_select");

//ロードされたとき
async function onLoad(evt) {
    //基本情報の問題一覧を取得する
    const req = await fetch(base_url + "/get_fe_mondais", { method: "GET" });

    //問題リスト
    const mondai_list = await req.json();

    //リストを逆から回す
    Object.keys(mondai_list).reverse().forEach((key) => {
        //選択肢を追加する
        const add_option = document.createElement("option");
        add_option.value = key;
        add_option.textContent = mondai_list[key];

        //要素を追加する
        fe_menjo_mondai_select.appendChild(add_option);
    });

    //デバッグ状態の時
    if (debug_mode) {
        //問題を選択する
        fe_menjo_mondai_select.value = "20221211";

        //読み込むボタンを押す
        Mondai_Load_Button.click();
    }
}

//読み込み完了イベント
window.addEventListener("DOMContentLoaded", onLoad);

//問題をロードするボタン
const Mondai_Load_Button = document.querySelector("#Mondai_Load_Button");

//問題のPDFを開くボタン
const Mondai_Open_Button = document.querySelector("#Mondai_Open_Button");

//PDFのURL
let mondai_url = "";

//ロードボタンが押されたとき
Mondai_Load_Button.addEventListener("click", async function (elem) {
    try {
        //ロード画面を表示する
        overlay_message.innerText = "問題を取得しています";
        show_load();

        //選択した問題IDを取得
        const send_val = fe_menjo_mondai_select.value;

        //問題が選択されていなかったとき
        if (send_val == -1) {
            alert("問題を選択してください");
            hide_load();
            return;
        }

        //解答欄を更新するか
        let is_clear = false;

        //デバッグモード
        if (debug_mode) {
            //解答欄を更新する
            is_clear = true;
        } else {
            //解答欄を更新するかを聞く
            is_clear = window.confirm("解答欄を更新しますか?");
        }

        //問題の情報を取得
        const req = await fetch(base_url + "/get_mondai/fe/" + send_val, { method: "GET" });

        //JSON形式に変換
        const mondais_data = await req.json();

        //問題を表示する
        show_mondai(mondais_data["data"], is_clear);

        //PDFのURLを設定する
        mondai_url = mondais_data["mondai_url"];

    } catch (ex) {
        alert("問題の取得に失敗しました");
    }

    //ロード画面を隠す
    hide_load();
})

//問題PDFを開くボタンを押したとき
Mondai_Open_Button.addEventListener("click", function (evt) {
    //PDFのURLが設定されているとき
    if (mondai_url != "") {
        //PDFをポップアップで開く
        window.open(mondai_url, null, 'width=1200,toolbar=yes,menubar=yes,scrollbars=yes');
    } else {
        alert("問題を読み込んでください");
    }
})

//結果保存ボタン
const Save_Result_Button = document.querySelector("#Save_Result_Button");

//保存ボタンが押されたとき
Save_Result_Button.addEventListener("click",function(elem){
    //結果が設定されているとき
    if (report_str == "") {
        alert("結果が存在しません");
        return
    }
    
    //結果をhtmlに書き出す
    dl_text(report_str,"Report.html");
})

//解答欄が更新されたとき
kaitouran.addEventListener("change",function(evt){
    let targetid = evt.target.id;
    let target_val = evt.target.value;
    let basetr = evt.target.closest("tr");

    if (targetid == "input_answer") {
        console.log(basetr.id);
        console.log(target_val);
    }; 
});