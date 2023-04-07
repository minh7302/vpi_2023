# VPI_new
*) api/auth: Chứa các API - một phần của chương trình quản lý dữ liệu, được sử dụng để xác thực người dùng và quản lý quyền truy cập. Các module này sử dụng FastAPI để xác thực người dùng thông qua access_token và quản lý quyền truy cập thông qua role và permission.
	- Các thông số sau đây có thể được định cấu hình:
	JWT_PRIVATE_KEY: chuỗi khóa bí mật sử dụng để mã hóa và giải mã access_token.
	JWT_ALGORITHM: thuật toán mã hóa được sử dụng để mã hóa và giải mã access_token.
	ACCESS_TOKEN_EXPIRE_DAYS: số ngày mà access_token có hiệu lực.

*) static: chứa các file css và js để căn chỉnh giao diện, thực hiện chức năng trên trang web

*) templates: chứa các file html
	home.html : giao diện chính của web
	import_file.html: giao diện phần import file trong home.html
	login.html: Giao diện login

*) File app chứa các api cần thiết cho thiết kế trang web

*) File config.py chứa các thiết lập cấu hình cho ứng dụng.
	- Các thiết lập
	POSTGRES_PORT: Cổng kết nối đến cơ sở dữ liệu PostgreSQL.
	POSTGRES_PASSWORD: Mật khẩu để kết nối đến cơ sở dữ liệu PostgreSQL.
	POSTGRES_USER: Tên người dùng để kết nối đến cơ sở dữ liệu PostgreSQL.
	POSTGRES_DB: Tên cơ sở dữ liệu PostgreSQL để kết nối đến.
	POSTGRES_HOST: Địa chỉ máy chủ PostgreSQL để kết nối đến.
	JWT_PRIVATE_KEY: Khóa bí mật để tạo mã thông báo JWT.
	JWT_ALGORITHM: Thuật toán được sử dụng để tạo mã thông báo JWT.
	REFRESH_TOKEN_EXPIRE_DAYS: Số ngày hết hạn cho mã thông báo làm mới.
	ACCESS_TOKEN_EXPIRE_DAYS: Số ngày hết hạn cho mã thông báo truy cập.
	- Tệp cấu hình
	.env: Tệp cấu hình cho ứng dụng.

*) File dashapp.py: sử dụng framework Dash để tạo giao diện web. Ứng dụng này cho phép người dùng chọn một giá trị Well_ID và vẽ đồ thị dựa trên các giá trị trong database. Ứng dụng này có hai trang, mỗi trang có một layout khác nhau:
+) Trang 1
	- Input:
	. well_id (dcc.Input): đây là input box cho phép người dùng nhập Well_ID
	. my-checkboxes (dcc.Checklist): đây là danh sách các checkbox cho phép người dùng chọn các giá trị để vẽ đồ thị.
	- Output:
	graph (dcc.Graph): đây là đồ thị được vẽ dựa trên các giá trị được chọn từ my-checkboxes.
	- Callbacks:
	. update_checklist_options: callback này trả về danh sách các giá trị curve_id cho phép người dùng chọn từ Well_ID được chọn.
	. update_checklist_value: callback này trả về danh sách các giá trị được chọn từ my-checkboxes. Nếu giá trị all được chọn thì tất cả các giá trị khác sẽ được chọn.
	. update_graph: callback này lấy các giá trị được chọn từ my-checkboxes và well_id để vẽ đồ thị.
+ Trang 2
	- Input:
	. well_id1 (dcc.Dropdown): đây là dropdown list cho phép người dùng chọn các giá trị Well_ID.
	. my-radioitems (dcc.RadioItems): đây là danh sách các radio button cho phép người dùng chọn các giá trị để vẽ đồ thị.
	- Output:
	. graph1 (dcc.Graph): đây là đồ thị được vẽ dựa trên các giá trị được chọn từ my-radioitems.
	- Callbacks:
	. update_radioitems_options: callback này trả về danh sách các giá trị curve_id cho phép người dùng chọn từ Well_ID được chọn.
	. update_graph1: callback này lấy các giá trị được chọn từ my-radioitems và well_id1 để vẽ đồ thị.

*) File db_connect.py chứa các cấu hình và kết nối tới cơ sở dữ liệu, bao gồm các phương thức sau:
	- create_engine: tạo engine kết nối tới cơ sở dữ liệu, dựa trên DATABASE_URL được cấu hình trong file config.py.
	- sessionmaker: tạo session để thực hiện các truy vấn tới cơ sở dữ liệu, với các cấu hình autocommit=False, autoflush=False và bind=engine.
	declarative_base: tạo một base class để khai báo các models dựa trên ORM.
	- MetaData: tạo metadata object để định nghĩa các bảng trong cơ sở dữ liệu.
	metadata.reflect: đọc cấu trúc của cơ sở dữ liệu và tự động tạo các đối tượng bảng tương ứng.
	- get_db: trả về một session tới cơ sở dữ liệu, sử dụng yield để tạo một generator function.
Các phương thức và biến được import từ các module sqlalchemy, config và sqlalchemy.orm. Tên và thông tin về cơ sở dữ liệu được lưu trữ trong biến DATABASE_URL.

*) File models.py này định nghĩa các models (mô hình) cho các đối tượng trong cơ sở dữ liệu.
	- User: đối tượng tương ứng với bảng user trong cơ sở dữ liệu.
	- Curve_value: đối tượng tương ứng với bảng cal_curve_value trong cơ sở dữ liệu.
	- Per_mission: đối tượng tương ứng với bảng permission trong cơ sở dữ liệu.
Các models này được định nghĩa bằng cách kế thừa từ lớp Base được import từ module db_connect. Các thuộc tính và phương thức của các models được xác định bằng cách sử dụng các thông tin về cấu trúc của bảng trong cơ sở dữ liệu thông qua biến metadata.

*) File schemas.py này bao gồm các định dạng dữ liệu (schemas) cho các đối tượng User, Curve và Authentication.
	- User_base: định dạng cơ bản cho đối tượng User, bao gồm các thuộc tính user_id, user_name và role.
	- UserInDb: mở rộng định dạng cơ bản User_base bằng cách thêm thuộc tính password.
	- Update_user: định dạng cho việc cập nhật thông tin User, bao gồm các thuộc tính user_name và role.
	- New_user: định dạng cho việc tạo mới User, bao gồm các thuộc tính user_id, user_name, password và role.
	- Curve_value_out: định dạng cho đối tượng Curve, bao gồm các thuộc tính curve_id, md, cal_value và well_id.
	- Token: định dạng cho đối tượng Token, bao gồm các thuộc tính access_token và token_type.
	- TokenData: định dạng cho thông tin trong Token, bao gồm thuộc tính username.
Tất cả các định dạng đều được xác định bằng Pydantic BaseModel và có thêm cấu hình orm_mode=True để cho phép sử dụng chúng trong ORM (Object-Relational Mapping).
